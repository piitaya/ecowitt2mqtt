"""Define MQTT publishing."""
# pylint: disable=unused-argument
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, TypedDict

from asyncio_mqtt import Client, MqttError

from ecowitt2mqtt.backports.enum import StrEnum
from ecowitt2mqtt.config import Config
from ecowitt2mqtt.const import (
    DATA_POINT_BEAUFORT_SCALE,
    DATA_POINT_CO2,
    DATA_POINT_CO2_24H,
    DATA_POINT_DAILY_RAIN,
    DATA_POINT_DEWPOINT,
    DATA_POINT_EVENT_RAIN,
    DATA_POINT_FEELSLIKE,
    DATA_POINT_FROST_POINT,
    DATA_POINT_FROST_RISK,
    DATA_POINT_GLOB_BAROM,
    DATA_POINT_GLOB_BATT,
    DATA_POINT_GLOB_GAIN_PIEZO,
    DATA_POINT_GLOB_GUST,
    DATA_POINT_GLOB_HUMIDITY,
    DATA_POINT_GLOB_LEAK,
    DATA_POINT_GLOB_MOISTURE,
    DATA_POINT_GLOB_PM10,
    DATA_POINT_GLOB_PM25,
    DATA_POINT_GLOB_R_RAIN,
    DATA_POINT_GLOB_RAIN,
    DATA_POINT_GLOB_RAIN_PIEZO,
    DATA_POINT_GLOB_TEMP,
    DATA_POINT_GLOB_TF,
    DATA_POINT_GLOB_VOLT,
    DATA_POINT_GLOB_WETNESS,
    DATA_POINT_GLOB_WIND,
    DATA_POINT_GLOB_WINDDIR,
    DATA_POINT_HEATINDEX,
    DATA_POINT_HOURLY_RAIN,
    DATA_POINT_HUMI_CO2,
    DATA_POINT_HUMIDEX,
    DATA_POINT_HUMIDEX_PERCEPTION,
    DATA_POINT_HUMIDITY_ABS,
    DATA_POINT_HUMIDITY_ABS_IN,
    DATA_POINT_INTERVAL,
    DATA_POINT_LIGHTNING,
    DATA_POINT_LIGHTNING_NUM,
    DATA_POINT_LIGHTNING_TIME,
    DATA_POINT_MONTHLY_RAIN,
    DATA_POINT_R_RAIN_PIEZO,
    DATA_POINT_RAIN_RATE,
    DATA_POINT_RELATIVE_STRAIN_INDEX,
    DATA_POINT_RELATIVE_STRAIN_INDEX_PERCEPTION,
    DATA_POINT_RUNTIME,
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_1,
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_2,
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_3,
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_4,
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_5,
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_6,
    DATA_POINT_SIMMER_INDEX,
    DATA_POINT_SIMMER_ZONE,
    DATA_POINT_SOLARRADIATION,
    DATA_POINT_SOLARRADIATION_PERCEIVED,
    DATA_POINT_TF_CO2,
    DATA_POINT_THERMAL_PERCEPTION,
    DATA_POINT_TOTAL_RAIN,
    DATA_POINT_UV,
    DATA_POINT_WEEKLY_RAIN,
    DATA_POINT_WINDCHILL,
    DATA_POINT_WS90_VER,
    DATA_POINT_YEARLY_RAIN,
    LOGGER,
)
from ecowitt2mqtt.data import ProcessedData
from ecowitt2mqtt.helpers.calculator import CalculatedDataPoint, DataPointType
from ecowitt2mqtt.helpers.calculator.battery import (
    BatteryStrategy,
    get_battery_strategy,
)
from ecowitt2mqtt.helpers.device import Device
from ecowitt2mqtt.helpers.publisher import MqttPublisher, generate_mqtt_payload
from ecowitt2mqtt.helpers.typing import CalculatedValueType


class DeviceClass(StrEnum):
    """Define a device class enum."""

    BATTERY = "battery"
    CO2 = "carbon_dioxide"
    DURATION = "duration"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    IRRADIANCE = "irradiance"
    MOISTURE = "moisture"
    PM10 = "pm10"
    PM25 = "pm25"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    TIMESTAMP = "timestamp"
    VOLTAGE = "voltage"


class EntityCategory(StrEnum):
    """Define an entity category enum."""

    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"


class Platform(StrEnum):
    """Define a platform enum."""

    BINARY_SENSOR = "binary_sensor"
    SENSOR = "sensor"


class StateClass(StrEnum):
    """Define a state class enum."""

    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"


class DeviceType(TypedDict):
    """Define a type that represents a Home Assistant device."""

    identifiers: list[str]
    manufacturer: str
    model: str
    name: str
    sw_version: str


@dataclass
class EntityDescription:
    """Define a description (set of characteristics) of a Home Assistant entity."""

    device_class: str | None = None
    entity_category: str | None = None
    icon: str | None = None
    state_class: str | None = None


@dataclass
class HassDiscoveryPayload:
    """Define a MQTT Discovery configuration for an entity."""

    payload: dict[str, Any]
    topic: str


AVAILABILITY_OFFLINE = "offline"
AVAILABILITY_ONLINE = "online"

DATA_POINT_BATTERY_BOOLEAN = "battery_boolean"
DATA_POINT_BATTERY_NUMERIC = "battery_numeric"
DATA_POINT_BATTERY_PERCENTAGE = "battery_percentage"

ENTITY_DESCRIPTIONS = {
    DATA_POINT_BATTERY_BOOLEAN: EntityDescription(
        device_class=DeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DATA_POINT_BATTERY_NUMERIC: EntityDescription(
        device_class=DeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_BATTERY_PERCENTAGE: EntityDescription(
        device_class=DeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_BEAUFORT_SCALE: EntityDescription(
        icon="mdi:weather-windy",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_CO2: EntityDescription(
        device_class=DeviceClass.CO2,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_CO2_24H: EntityDescription(
        device_class=DeviceClass.CO2,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_DEWPOINT: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_FEELSLIKE: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_FROST_POINT: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_FROST_RISK: EntityDescription(
        icon="mdi:snowflake-alert",
    ),
    DATA_POINT_GLOB_BAROM: EntityDescription(
        device_class=DeviceClass.PRESSURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_GAIN_PIEZO: EntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DATA_POINT_GLOB_GUST: EntityDescription(
        icon="mdi:weather-windy",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_HUMIDITY: EntityDescription(
        device_class=DeviceClass.HUMIDITY,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_LEAK: EntityDescription(
        device_class=DeviceClass.MOISTURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_MOISTURE: EntityDescription(
        icon="mdi:water-percent",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_PM10: EntityDescription(
        device_class=DeviceClass.PM10,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_PM25: EntityDescription(
        device_class=DeviceClass.PM25,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_R_RAIN: EntityDescription(
        icon="mdi:water",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_RAIN: EntityDescription(
        icon="mdi:water",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_RAIN_PIEZO: EntityDescription(
        icon="mdi:water",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_TEMP: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_TF: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_VOLT: EntityDescription(
        device_class=DeviceClass.VOLTAGE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_WETNESS: EntityDescription(
        icon="mdi:water-percent",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_WIND: EntityDescription(
        icon="mdi:weather-windy",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_GLOB_WINDDIR: EntityDescription(
        icon="mdi:compass",
    ),
    DATA_POINT_HEATINDEX: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_HUMIDEX: EntityDescription(
        icon="mdi:water",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_HUMIDEX_PERCEPTION: EntityDescription(
        icon="mdi:water",
    ),
    DATA_POINT_HUMI_CO2: EntityDescription(
        device_class=DeviceClass.HUMIDITY,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_HUMIDITY_ABS: EntityDescription(
        icon="mdi:water-percent",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_HUMIDITY_ABS_IN: EntityDescription(
        icon="mdi:water-percent",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_INTERVAL: EntityDescription(
        icon="mdi:water-percent",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DATA_POINT_LIGHTNING: EntityDescription(
        icon="mdi:map-marker-distance",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_LIGHTNING_NUM: EntityDescription(
        icon="mdi:weather-lightning",
        state_class=StateClass.TOTAL,
    ),
    DATA_POINT_LIGHTNING_TIME: EntityDescription(
        device_class=DeviceClass.TIMESTAMP,
    ),
    DATA_POINT_R_RAIN_PIEZO: EntityDescription(
        icon="mdi:water",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_1: EntityDescription(
        icon="mdi:timer",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_2: EntityDescription(
        icon="mdi:timer",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_3: EntityDescription(
        icon="mdi:timer",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_4: EntityDescription(
        icon="mdi:timer",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_5: EntityDescription(
        icon="mdi:timer",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SAFE_EXPOSURE_TIME_SKIN_TYPE_6: EntityDescription(
        icon="mdi:timer",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SIMMER_INDEX: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SIMMER_ZONE: EntityDescription(
        icon="mdi:heat-wave",
    ),
    DATA_POINT_SOLARRADIATION: EntityDescription(
        device_class=DeviceClass.IRRADIANCE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_SOLARRADIATION_PERCEIVED: EntityDescription(
        icon="mdi:weather-sunny",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_RAIN_RATE: EntityDescription(
        icon="mdi:water",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_RELATIVE_STRAIN_INDEX: EntityDescription(
        icon="mdi:heat-wave",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_RELATIVE_STRAIN_INDEX_PERCEPTION: EntityDescription(
        icon="mdi:heat-wave",
    ),
    DATA_POINT_RUNTIME: EntityDescription(
        device_class=DeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_THERMAL_PERCEPTION: EntityDescription(
        icon="mdi:water",
    ),
    DATA_POINT_TF_CO2: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_UV: EntityDescription(
        icon="mdi:weather-sunny",
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_WINDCHILL: EntityDescription(
        device_class=DeviceClass.TEMPERATURE,
        state_class=StateClass.MEASUREMENT,
    ),
    DATA_POINT_WS90_VER: EntityDescription(entity_category=EntityCategory.DIAGNOSTIC),
}

PLATFORM_MAP = {
    DataPointType.BOOLEAN: Platform.BINARY_SENSOR,
    DataPointType.NON_BOOLEAN: Platform.SENSOR,
}

STATE_CLASS_OVERRIDES = {
    DATA_POINT_DAILY_RAIN: StateClass.TOTAL,
    DATA_POINT_EVENT_RAIN: StateClass.TOTAL,
    DATA_POINT_GLOB_RAIN_PIEZO: StateClass.TOTAL,
    DATA_POINT_HOURLY_RAIN: StateClass.TOTAL,
    DATA_POINT_MONTHLY_RAIN: StateClass.TOTAL,
    DATA_POINT_TOTAL_RAIN: StateClass.TOTAL,
    DATA_POINT_WEEKLY_RAIN: StateClass.TOTAL,
    DATA_POINT_YEARLY_RAIN: StateClass.TOTAL,
}


def get_availability_payload(
    data_point: CalculatedDataPoint,
) -> str:
    """Get the availability payload for a data point.

    Right now, this is hardcoded to always available.

    Args:
        data_point: A parsed CalculatedDataPoint object.

    Returns:
        An availability string.
    """
    return AVAILABILITY_ONLINE


class HomeAssistantDiscoveryPublisher(
    MqttPublisher
):  # pylint: disable=too-few-public-methods
    """Define an MQTT publisher for the MQTT Discovery standard."""

    def __init__(self, config: Config, client: Client) -> None:
        """Initialize.

        Args:
            config: A Config object.
            client: An MQTT Client object.
        """
        super().__init__(config, client)

        self._discovery_payloads: dict[str, HassDiscoveryPayload] = {}

    def _generate_discovery_payload(  # pylint: disable=too-many-branches
        self, device: Device, payload_key: str, data_point: CalculatedDataPoint
    ) -> HassDiscoveryPayload:
        """Generate a discovery payload for an entity.

        Args:
            device: A Device object.
            payload_key: The Ecowitt payload key.
            data_point: A CalculatedDataPoint object.

        Returns:
            A parsed HassDiscoveryPayload object.
        """
        # Since batteries can be one of many different strategies, we calculate an
        # entity description at runtime:
        if data_point.data_point_key in (DATA_POINT_GLOB_BATT, DATA_POINT_GLOB_VOLT):
            strategy = get_battery_strategy(self._config, payload_key)
            if strategy == BatteryStrategy.BOOLEAN:
                data_point_key = DATA_POINT_BATTERY_BOOLEAN
            elif strategy == BatteryStrategy.NUMERIC:
                data_point_key = DATA_POINT_BATTERY_NUMERIC
            else:
                data_point_key = DATA_POINT_BATTERY_PERCENTAGE
        else:
            data_point_key = data_point.data_point_key

        base_topic = (
            f"{self._config.hass_discovery_prefix}/{PLATFORM_MAP[data_point.data_type]}"
            f"/{device.unique_id}/{payload_key}"
        )

        config = {
            "availability_topic": f"{base_topic}/availability",
            "device": {
                "identifiers": [device.unique_id],
                "manufacturer": device.manufacturer,
                "model": device.model,
                "name": device.name,
                "sw_version": device.station_type,
            },
            "json_attributes_topic": f"{base_topic}/attributes",
            "name": payload_key,
            "qos": 1,
            "retain": self._config.mqtt_retain,
            "state_topic": f"{base_topic}/state",
            "unique_id": f"{device.unique_id}_{payload_key}",
        }
        if self._config.hass_entity_id_prefix:
            config["object_id"] = f"{self._config.hass_entity_id_prefix}_{payload_key}"

        payload = self._discovery_payloads[payload_key] = HassDiscoveryPayload(
            config, f"{base_topic}/config"
        )

        if data_point.attributes:
            payload.payload["json_attributes_topic"] = f"{base_topic}/attributes"
        if data_point.unit:
            payload.payload["unit_of_measurement"] = data_point.unit

        # If we have an entity description, use it:
        if description := ENTITY_DESCRIPTIONS.get(data_point_key):
            for discovery_key, value in (
                ("device_class", description.device_class),
                ("entity_category", description.entity_category),
                ("icon", description.icon),
                (
                    "state_class",
                    STATE_CLASS_OVERRIDES.get(payload_key, description.state_class),
                ),
            ):
                if not value:
                    continue
                payload.payload[discovery_key] = value
        else:
            LOGGER.debug(
                'Missing entity description for "%s" (please report it!)',
                payload_key,
            )

        return payload

    async def async_publish(self, data: dict[str, CalculatedValueType]) -> None:
        """Publish to MQTT.

        Args:
            data: A data payload.

        Raises:
            MqttError: Raised on any MQTT error.
        """
        processed_data = ProcessedData(self._config, data)
        tasks: list[asyncio.Task] = []

        try:
            for payload_key, data_point in processed_data.output.items():
                discovery_payload = self._generate_discovery_payload(
                    processed_data.device, payload_key, data_point
                )

                for topic, payload in (
                    (discovery_payload.topic, discovery_payload.payload),
                    (
                        discovery_payload.payload["availability_topic"],
                        get_availability_payload(data_point),
                    ),
                    (
                        discovery_payload.payload["json_attributes_topic"],
                        data_point.attributes,
                    ),
                    (
                        discovery_payload.payload["state_topic"],
                        data_point.value,
                    ),
                ):
                    tasks.append(
                        asyncio.create_task(
                            self._client.publish(
                                topic,
                                payload=generate_mqtt_payload(payload),
                                retain=self._config.mqtt_retain,
                            )
                        )
                    )

                    await asyncio.gather(*tasks)
        except MqttError:
            for task in tasks:
                task.cancel()
            raise

        LOGGER.info("Published to Home Assistant MQTT Discovery")
        LOGGER.debug("Published data: %s", processed_data.output)
