import sys, datetime
class FixedPendulum:
    @staticmethod
    def now(): return datetime.datetime.now()
    @staticmethod  
    def today(): return datetime.date.today()
    def __init__(self, *args, **kwargs): pass
pendulum_module = type(sys)('pendulum')
pendulum_module.now = FixedPendulum.now
pendulum_module.today = FixedPendulum.today  
pendulum_module.Pendulum = FixedPendulum
pendulum_module.__version__ = '2.1.2'
sys.modules['pendulum'] = pendulum_module
