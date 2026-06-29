"""
Execution Engine — the core ETL orchestrator.
Reads pipeline metadata, drives the ETL flow, logs every step.
"""
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.connectors.factory import create_connector
from app.connectors.base import DataFlowException
from app.core.security import decrypt_value
from app.models.job import JobRun, JobRunLog, RejectedRecord
from app.models.pipeline import Pipeline, Checkpoint
from app.services import transform_service, validation_service


def _build_conn_config(conn) -> dict:
    """Assemble decrypted config dict from a Connection ORM object."""
    password = None
    if conn.encrypted_password:
        try:
            password = decrypt_value(conn.encrypted_password)
        except Exception:
            password = conn.encrypted_password  # fallback if not encrypted yet

    return {
        "host": conn.host,
        "port": conn.port,
        "database_name": conn.database_name,
        "username": conn.username,
        "password": password,
        "extra_config": conn.extra_config or {},
    }


class JobLogger:
    """Writes structured log entries for a job run — synced to DB + console."""

    def __init__(self, db: Session, job_run_id: str):
        self.db = db
        self.job_run_id = job_run_id

    def _write(self, level: str, stage: str, message: str, detail: dict = None):
        entry = JobRunLog(
            job_run_id=self.job_run_id,
            level=level,
            stage=stage,
            message=message,
            detail=detail or {},
        )
        self.db.add(entry)
        self.db.flush()
        print(f"[{level}][{stage}] {message}")

    def info(self, stage: str, message: str, detail: dict = None):
        self._write("INFO", stage, message, detail)

    def warn(self, stage: str, message: str, detail: dict = None):
        self._write("WARN", stage, message, detail)

    def error(self, stage: str, message: str, detail: dict = None):
        self._write("ERROR", stage, message, detail)


def run_pipeline(db: Session, pipeline_id: str, job_run_id: str, run_type: str = "MANUAL", test_limit: int = None):
    """
    Main ETL execution function. Called from Celery task.
    Uses a synchronous SQLAlchemy Session (Celery workers run sync).
    """
    job_run: JobRun = db.get(JobRun, job_run_id)
    logger = JobLogger(db, job_run_id)

    # Mark as RUNNING
    job_run.status = "RUNNING"
    job_run.started_at = datetime.now(timezone.utc)
    db.flush()

    source_connector = None
    target_connector = None

    try:
        # ── 1. Load Pipeline Metadata ────────────────────────────────────────
        logger.info("METADATA", "Pipeline metadata yükleniyor")
        pipeline: Pipeline = db.get(Pipeline, pipeline_id)
        if not pipeline:
            raise DataFlowException("PIPELINE_NOT_FOUND", f"Pipeline bulunamadı: {pipeline_id}")

        source_conn = pipeline.source_connection
        target_conn = pipeline.target_connection

        # ── 2. Create Connectors ─────────────────────────────────────────────
        logger.info("SOURCE_CONNECT", f"Kaynak bağlantısı başlatılıyor: {source_conn.name}")
        source_connector = create_connector(source_conn.type, _build_conn_config(source_conn))
        src_test = source_connector.test_connection()
        if not src_test.success:
            raise DataFlowException("SOURCE_CONNECTION_FAILED", f"Kaynak bağlanamadı: {src_test.error}", src_test.error)
        logger.info("SOURCE_CONNECTED", f"Kaynak bağlandı ({src_test.latency_ms}ms)")

        logger.info("TARGET_CONNECT", f"Hedef bağlantısı başlatılıyor: {target_conn.name}")
        target_connector = create_connector(target_conn.type, _build_conn_config(target_conn))
        tgt_test = target_connector.test_connection()
        if not tgt_test.success:
            raise DataFlowException("TARGET_CONNECTION_FAILED", f"Hedef bağlanamadı: {tgt_test.error}", tgt_test.error)
        logger.info("TARGET_CONNECTED", f"Hedef bağlandı ({tgt_test.latency_ms}ms)")

        # ── 3. Checkpoint (Incremental) ──────────────────────────────────────
        checkpoint_value = None
        if pipeline.load_strategy == "INCREMENTAL":
            cp: Checkpoint = pipeline.checkpoint
            if cp:
                checkpoint_value = cp.checkpoint_value
                logger.info("CHECKPOINT", f"Son checkpoint: {checkpoint_value} [{cp.checkpoint_column}]")
            else:
                logger.info("CHECKPOINT", "İlk incremental çalışma — checkpoint yok")

        # ── 4. Read Source ───────────────────────────────────────────────────
        logger.info("SOURCE_READ_START", "Kaynak veri okunuyor")
        read_config = {
            "table": pipeline.source_config.get("table"),
            "query": pipeline.source_config.get("query"),
            "checkpoint_col": pipeline.source_config.get("checkpoint_col"),
            "checkpoint_value": checkpoint_value,
            "limit": test_limit,
            "batch_size": pipeline.batch_size,
        }
        df = source_connector.read_data(read_config)
        source_count = len(df)
        job_run.source_count = source_count
        logger.info("SOURCE_READ_DONE", f"{source_count:,} satır okundu", {"count": source_count})

        if source_count == 0:
            logger.info("NO_DATA", "Kaynak veri boş — iş tamamlandı")
            _finish_success(db, job_run, source_count=0, success_count=0, rejected_count=0)
            return

        # ── 5. Column Mapping & Transforms ──────────────────────────────────
        active_mappings = [m for m in pipeline.column_mappings if not m.is_excluded]
        if active_mappings:
            logger.info("MAPPING", f"{len(active_mappings)} kolon eşleştirmesi uygulanıyor")
            df = transform_service.apply_transforms(df, active_mappings)
            logger.info("TRANSFORM_DONE", "Dönüşümler tamamlandı")

        # ── 6. Validation ────────────────────────────────────────────────────
        if pipeline.validation_rules:
            logger.info("VALIDATION_START", f"{len(pipeline.validation_rules)} validation kuralı çalıştırılıyor")
            v_result = validation_service.validate(df, pipeline.validation_rules)

            if v_result.warnings:
                for w in v_result.warnings:
                    logger.warn("VALIDATION_WARN", w)

            if v_result.rejected_records:
                _save_rejected(db, job_run_id, pipeline_id, v_result.rejected_records)
                logger.warn("VALIDATION_DONE", f"{len(v_result.rejected_records)} kayıt reddedildi")
                job_run.rejected_count = len(v_result.rejected_records)

            df = v_result.valid_df
            logger.info("VALIDATION_DONE", f"Validation tamamlandı: {len(df):,} geçerli kayıt")
        else:
            job_run.rejected_count = 0

        # ── 7. Write to Target ───────────────────────────────────────────────
        logger.info("TARGET_WRITE_START", f"Hedefe yazılıyor: {pipeline.load_strategy}")
        write_config = {
            "table": pipeline.target_config.get("table"),
            "mode": pipeline.load_strategy,
            "upsert_keys": pipeline.upsert_keys or [],
            "create_if_not_exists": pipeline.target_config.get("create_if_not_exists", False),
        }
        write_result = target_connector.write_data(df, write_config)
        logger.info("TARGET_WRITE_DONE", f"{write_result.rows_written:,} satır yazıldı", {"rows_written": write_result.rows_written})

        # ── 8. Update Checkpoint ─────────────────────────────────────────────
        if pipeline.load_strategy == "INCREMENTAL" and source_count > 0:
            cp_col = pipeline.source_config.get("checkpoint_col")
            if cp_col and cp_col in df.columns:
                new_val = str(df[cp_col].max())
                cp = pipeline.checkpoint or Checkpoint(pipeline_id=pipeline_id, checkpoint_column=cp_col)
                cp.checkpoint_value = new_val
                cp.checkpoint_column = cp_col
                db.merge(cp)
                logger.info("CHECKPOINT_UPDATED", f"Checkpoint güncellendi: {new_val}")

        # ── 9. Finish ────────────────────────────────────────────────────────
        logger.info("JOB_SUCCESS", "İş başarıyla tamamlandı 🎉")
        _finish_success(
            db, job_run,
            source_count=source_count,
            success_count=write_result.rows_written,
            rejected_count=job_run.rejected_count or 0,
        )

    except DataFlowException as e:
        logger.error("JOB_FAILED", e.message, {"code": e.code, "detail": e.detail})
        _finish_failed(db, job_run, e.message, e.detail)
        raise

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("JOB_FAILED", f"Beklenmeyen hata: {str(e)}", {"traceback": tb})
        _finish_failed(db, job_run, f"Beklenmeyen hata: {str(e)}", tb)
        raise

    finally:
        if source_connector:
            source_connector.close()
        if target_connector:
            target_connector.close()
        db.commit()


def _finish_success(db, job_run: JobRun, source_count: int, success_count: int, rejected_count: int):
    now = datetime.now(timezone.utc)
    job_run.status = "SUCCESS"
    job_run.finished_at = now
    job_run.source_count = source_count
    job_run.success_count = success_count
    job_run.target_count = success_count
    job_run.rejected_count = rejected_count
    job_run.error_count = 0
    if job_run.started_at:
        job_run.duration_seconds = (now - job_run.started_at).total_seconds()


def _finish_failed(db, job_run: JobRun, message: str, detail: str = None):
    now = datetime.now(timezone.utc)
    job_run.status = "FAILED"
    job_run.finished_at = now
    job_run.error_message = message
    job_run.error_detail = detail
    if job_run.started_at:
        job_run.duration_seconds = (now - job_run.started_at).total_seconds()


def _save_rejected(db, job_run_id: str, pipeline_id: str, records):
    for rec in records:
        db.add(RejectedRecord(
            job_run_id=job_run_id,
            pipeline_id=pipeline_id,
            row_number=rec.row_number,
            source_data=rec.source_data,
            error_column=rec.error_column,
            error_rule=rec.error_rule,
            error_message=rec.error_message,
        ))
