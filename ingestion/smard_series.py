"""Which SMARD series we download.

Filter IDs come from the community API docs at https://smard.api.bund.dev.
Volumes are MWh per quarter-hour. The price is EUR/MWh.
"""

from dataclasses import dataclass

# Every series below exists in 15-minute steps. For the price, SMARD repeats
# each hourly value four times before the market moved to 15 minutes (Oct 2025).
RESOLUTION = "quarterhour"


@dataclass(frozen=True)
class SmardSeries:
    filter_id: int
    name: str
    region: str = "DE"


SERIES = [
    # Day-ahead price of the Germany/Luxembourg bidding zone
    SmardSeries(4169, "price_day_ahead", region="DE-LU"),
    # Actual generation by source
    SmardSeries(4068, "gen_solar"),
    SmardSeries(4067, "gen_wind_onshore"),
    SmardSeries(1225, "gen_wind_offshore"),
    SmardSeries(4066, "gen_biomass"),
    SmardSeries(1226, "gen_hydro"),
    SmardSeries(1228, "gen_other_renewables"),
    SmardSeries(1224, "gen_nuclear"),
    SmardSeries(1223, "gen_lignite"),
    SmardSeries(4069, "gen_hard_coal"),
    SmardSeries(4071, "gen_natural_gas"),
    SmardSeries(4070, "gen_pumped_storage"),
    SmardSeries(1227, "gen_other_conventional"),
    # Consumption. Residual load is total load minus wind and solar.
    SmardSeries(410, "load_total"),
    SmardSeries(4359, "load_residual"),
    # Day-ahead forecasts from the grid operators
    SmardSeries(123, "forecast_wind_onshore"),
    SmardSeries(3791, "forecast_wind_offshore"),
    SmardSeries(125, "forecast_solar"),
]
