from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class SiteMetaLocation(BaseModel):
    lat: float
    lon: float
    source: Literal["ground_telescope", "orbital_imagery"]


class MissionProfile(BaseModel):
    crew_count: int = Field(ge=2, le=4)
    max_stay_days: int = Field(ge=1, le=60)
    mission_type: Literal["mobile_trailer_depot", "permanent_main_base"]


class SiteMeta(BaseModel):
    site_id: str
    celestial_body: Literal["moon", "mars", "asteroid_other"]
    location: SiteMetaLocation
    mission_profile: MissionProfile


class BayesConfig(BaseModel):
    prior_p_qualified: float = Field(ge=0, le=1)
    uncertainty_weight: float = Field(ge=0, le=1)
    veto_threshold: float = Field(ge=0, le=1)
    enable_coexistence_check: bool


class TerrainFeature(BaseModel):
    slope_mean_deg: float
    slope_max_deg: float
    boulder_density_over_30cm: float
    micro_roughness_score: float = Field(ge=0, le=1)
    p_likelihood: float = Field(ge=0, le=1)


class IlluminationFeature(BaseModel):
    continuous_sun_hours: float
    terrain_shade_available: bool
    p_likelihood: float = Field(ge=0, le=1)


class CommsLOS(BaseModel):
    has_line_of_sight: bool
    p_likelihood: float = Field(ge=0, le=1)


class RadiationShield(BaseModel):
    terrain_shield_reduction_factor: float = Field(ge=0, le=1)
    p_likelihood: float = Field(ge=0, le=1)


class GeologyScience(BaseModel):
    outcrop_available: bool
    sampling_value_score: float = Field(ge=0, le=1)
    p_likelihood: float = Field(ge=0, le=1)


class CoexistenceAssessment(BaseModel):
    nearest_existing_site_distance_km: float
    inter_site_line_of_sight: bool
    route_max_slope_deg: float
    shared_ejecta_risk: float = Field(ge=0, le=1)
    p_likelihood: float = Field(ge=0, le=1)


class SpaceEnvironmentFeature(BaseModel):
    gcr_flux_estimate: float = Field(ge=0, le=1)
    spe_event_prob: float = Field(ge=0, le=1)
    micrometeor_flux: float = Field(ge=0, le=1)
    ejecta_flux_local: float = Field(ge=0, le=1)
    p_likelihood: float = Field(ge=0, le=1)


class GeneralFeatures(BaseModel):
    terrain: TerrainFeature
    illumination: IlluminationFeature
    comms_los: CommsLOS
    radiation_shield: RadiationShield
    geology_science: GeologyScience
    coexistence_assessment: Optional[CoexistenceAssessment] = None
    space_environment: Optional[SpaceEnvironmentFeature] = None


class MoonPlugin(BaseModel):
    lunar_day_night_risk: float = Field(ge=0, le=1)
    lunar_dust_risk: float = Field(ge=0, le=1)
    has_ice_nearby: bool


class MarsPlugin(BaseModel):
    dust_storm_prob: float = Field(ge=0, le=1)
    atm_pressure: float
    has_water_ice_near_surface: bool


class CelestialPlugin(BaseModel):
    moon: Optional[MoonPlugin] = None
    mars: Optional[MarsPlugin] = None


class RiskItem(BaseModel):
    feature_name: str
    risk_level: Literal["low", "medium", "high", "critical"]
    description: str


class AssessmentResult(BaseModel):
    p_site_qualified: float = Field(ge=0, le=1)
    uncertainty_std: float = Field(ge=0, le=1)
    veto_triggered: bool
    risk_items: List[RiskItem]


class ExoplanetSiteAssessment(BaseModel):
    site_meta: SiteMeta
    bayes_config: BayesConfig
    feature_groups: GeneralFeatures
    celestial_plugin: CelestialPlugin
    result: Optional[AssessmentResult] = None
