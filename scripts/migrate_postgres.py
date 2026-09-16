"""Explicit operator migration command. Never invoked by web/worker startup."""
from persistence.repository import get_storage_repository

def main():
    repository=get_storage_repository()
    try:
        if repository.backend!='postgresql': raise ValueError('PostgreSQL configuration required')
        repository.initialize()
        print('PostgreSQL additive migrations completed')
    except Exception:
        print('Migration failed; transaction rolled back. Review privately before retrying.')
        return 1
    finally:
        repository.close()
    return 0

if __name__=='__main__': raise SystemExit(main())
