from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from taburet import PackageManager

def pytest_funcarg__pm(request):
    engine = create_engine('postgresql://localhost/test_taburet', echo=False)
    session = sessionmaker(bind=engine)()
    request.addfinalizer(session.close)
    return PackageManager(session)