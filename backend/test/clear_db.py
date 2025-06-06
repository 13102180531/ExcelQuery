# scripts/clear_db.py

import sys
from pathlib import Path
import logging # For logging from the script itself

# Add project root to Python path to allow importing app modules
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import text

# Import all your SQLModel table definitions
from app.database.models import User, UserGroup, UploadedExcelFile # Add all your table models here
from app.core.config import settings # Your database URL

# Setup basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ALL_TABLE_MODELS = [
    UploadedExcelFile, # Table: uploaded_excel_files
    User,              # Table: app_users
    UserGroup,         # Table: user_groups
]
def clear_all_data(engine):
    if not SQLModel.metadata.tables:
        logger.error("No tables found in SQLModel.metadata. Ensure your models are imported.")
        return

    with Session(engine) as session:
        logger.info("Attempting to clear data from tables...")

        # Determine dialect for specific commands
        dialect_name = engine.dialect.name

        # Iterate in reverse order of model definition (assuming dependencies are handled this way)
        # This order is generally safer for DELETE operations due to foreign keys.
        for table_model in reversed(ALL_TABLE_MODELS):
            table_name = table_model.__tablename__

            use_truncate = False
            if dialect_name == "postgresql":
                truncate_sql = f"TRUNCATE TABLE \"{table_name}\" RESTART IDENTITY CASCADE;"
                use_truncate = True
            elif dialect_name == "mysql":
                # MySQL TRUNCATE does not support CASCADE directly in the TRUNCATE statement.
                # It implicitly resets auto-increment.
                # Foreign key checks need to be handled separately if they block TRUNCATE.
                # For simplicity here, we'll try a simple TRUNCATE.
                # A more robust MySQL approach might involve:
                # session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                # session.execute(text(f"TRUNCATE TABLE `{table_name}`;"))
                # session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                # This requires multiple execute calls and careful transaction management.
                # Let's try a simple TRUNCATE and let it fail if FKs are an issue,
                # then the DELETE fallback will be used.
                truncate_sql = f"TRUNCATE TABLE `{table_name}`;" # MySQL uses backticks for identifiers if needed
                use_truncate = True

            if use_truncate:
                try:
                    logger.info(f"Attempting to TRUNCATE table: {table_name} using command: {truncate_sql}")
                    session.execute(text(truncate_sql))
                    logger.info(f"Successfully TRUNCATED table: {table_name}")
                    # TRUNCATE on PostgreSQL with RESTART IDENTITY and MySQL implicitly handles auto-increment reset.
                    continue # Move to the next table
                except Exception as e:
                    logger.warning(f"Could not TRUNCATE table {table_name}. Error: {e}. Will attempt DELETE.")
                    # Fall through to DELETE if TRUNCATE fails

            # Fallback to DELETE FROM if not using TRUNCATE or if TRUNCATE failed
            try:
                logger.info(f"Attempting to DELETE FROM table: {table_name}")
                stmt = text(f"DELETE FROM \"{table_name}\"") # Use quotes for pg, adapt for others if needed
                if dialect_name == "mysql":
                    stmt = text(f"DELETE FROM `{table_name}`")
                elif dialect_name == "sqlite":
                     stmt = text(f"DELETE FROM {table_name}") # SQLite usually doesn't need quotes unless special chars

                session.execute(stmt)
                logger.info(f"Successfully DELETED data from table: {table_name}")

                # Reset auto-increment for SQLite if using DELETE
                if dialect_name == "sqlite":
                    try:
                        # This might fail if the table doesn't have an auto-incrementing PK
                        # or if sqlite_sequence doesn't have an entry yet.
                        session.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';"))
                        logger.info(f"Reset auto-increment for SQLite table: {table_name}")
                    except Exception as sqlite_seq_e:
                        logger.debug(f"Note: Could not reset sequence for {table_name} (may be normal): {sqlite_seq_e}")

            except Exception as e: # This is the except block that had the SyntaxError
                logger.error(f"Could not delete data from table {table_name}. Error: {e}")
                session.rollback()
                logger.error("Transaction rolled back due to error. Aborting further operations.")
                return # Stop if one table fails critically

        try:
            session.commit()
            logger.info("All data cleared successfully and transaction committed.")
        except Exception as e:
            logger.error(f"Failed to commit transaction after clearing data: {e}")
            session.rollback()
            logger.error("Transaction rolled back.")

    # This outer try-except is for broader issues, like connection problems
    # except Exception as e:
    #     logger.error(f"An unexpected error occurred during the data clearing process: {e}")

if __name__ == "__main__":
    logger.warning("This script will delete ALL data from the specified tables.")

    if not hasattr(settings, 'DATABASE_URL') or not settings.DATABASE_URL:
        logger.error("DATABASE_URL_SYNC is not defined in settings or is empty. Exiting.")
        sys.exit(1)

    logger.info(f"Database URL: {settings.DATABASE_URL}")

    engine = create_engine(settings.DATABASE_URL, echo=False) # Set echo=True for detailed SQL

    confirmation = input("Are you absolutely sure you want to proceed? (yes/no): ")
    if confirmation.lower() == "yes":
        try:
            clear_all_data(engine)
        except Exception as e:
            logger.critical(f"A critical error occurred: {e}", exc_info=True)
    else:
        logger.info("Operation cancelled by the user.")