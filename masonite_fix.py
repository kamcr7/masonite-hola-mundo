import sys, datetime
sys.modules['pendulum'] = type(sys)('pendulum')
sys.modules['pendulum'].now = datetime.datetime.now
sys.modules['pendulum'].today = datetime.date.today
sys.modules['pendulum'].__version__ = '2.1.2'
