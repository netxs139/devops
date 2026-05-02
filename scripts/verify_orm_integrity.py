import sys

from devops_collector.models.base_models import Base


# Import all plugin models
try:
    from devops_collector.plugins.gitlab.models import *
    from devops_collector.plugins.jira.models import *
    from devops_collector.plugins.sonarqube.models import *
    from devops_collector.plugins.zentao.models import *

    print(">>> All models imported successfully.")
except Exception as e:
    print(f">>> Error importing models: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Trigger relationship discovery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)
try:
    # This will trigger Mapper mapping and relationship validation
    Base.metadata.create_all(engine)
    print(">>> Metadata create_all successful.")
except Exception as e:
    print(f">>> Error during metadata discovery: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
