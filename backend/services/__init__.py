from services.auth import AuthService
from services.user import UserService
from services.farm import FarmService
from services.plot import PlotService
from services.disease import DiseaseService
from services.weather import WeatherService
from services.market import MarketService
from services.scheme import SchemeService
from services.notification import NotificationService

auth_service = AuthService()
user_service = UserService()
farm_service = FarmService()
plot_service = PlotService()
disease_service = DiseaseService()
weather_service = WeatherService()
market_service = MarketService()
scheme_service = SchemeService()
notification_service = NotificationService()

__all__ = [
    "auth_service",
    "user_service",
    "farm_service",
    "plot_service",
    "disease_service",
    "weather_service",
    "market_service",
    "scheme_service",
    "notification_service",
]
