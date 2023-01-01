from struct import unpack

def transform_temperature(value: list) -> float:
  parts = bytes(value[0:2])
  word = unpack('<h', parts)[0]
  return float(word)/10


def transform_air_volume(value: list) -> float:
  parts = value[0:2]
  word = unpack('<h', parts)[0]
  return float(word)

def transform_any(value: list) -> float:
  word = 0
  for n in range(len(value)):
      word += value[n]<<(n*8)
  return word

def transform_away(value: list) -> str:
    val = transform_any(value)
    if val == 7:
        return 'Yes'
    if val == 1:
        return 'No'
    return val

def transform_operating_mode(value: list) -> str:
    val = transform_any(value)
    if val == 255:
        return 'Auto'
    if val == 1:
        return 'Lim. Manual'
    if val == 5:
        return 'Manual'
    if val == 6:
        return 'Boost'
    if val == 11:
        return 'Away'
    return val

def transform_operating_mode2(value: list) -> str:
    val = transform_any(value)
    if val == 255:
        return 'Auto'
    if val == 1:
        return 'Manual'
    return val


# 8415 0601 00000000 100e0000 01	Set ventilation mode: supply only for 1 hour
# 8515 0601	Set ventilation mode: balance mode
# 8415 0301 00000000 ffffffff 00	Set temperature profile: normal
# 8415 0301 00000000 ffffffff 01	Set temperature profile: cool
# 8415 0301 00000000 ffffffff 02	Set temperature profile: warm
# 8415 0201 00000000 100e0000 01	Set bypass: activated for 1 hour
# 8415 0201 00000000 100e0000 02	Set bypass: deactivated for 1 hour
# 8515 0201	Set bypass: auto
# 031d 0104 00	Set sensor ventilation: temperature passive: off
# 031d 0104 01	Set sensor ventilation: temperature passive: auto only
# 031d 0104 02	Set sensor ventilation: temperature passive: on
# 031d 0106 00	Set sensor ventilation: humidity comfort: off
# 031d 0106 01	Set sensor ventilation: humidity comfort: auto only
# 031d 0106 02	Set sensor ventilation: humidity comfort: on
# 031d 0107 00	Set sensor ventilation: humidity protection: off
# 031d 0107 01	Set sensor ventilation: humidity protection: auto
# 031d 0107 02	Set sensor ventilation: humidity protection: on
commands = {
    'ventilation_level_0':    [0x84, 0x15, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00],
    'ventilation_level_1':    [0x84, 0x15, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01],
    'ventilation_level_2':    [0x84, 0x15, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02],
    'ventilation_level_3':    [0x84, 0x15, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x03],
    'bypass_activate_1h':     [0x84, 0x15, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x10, 0x0e, 0x00, 0x00, 0x01],
    'bypass_deactivate_1h':   [0x84, 0x15, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x10, 0x0e, 0x00, 0x00, 0x02],
    'bypass_auto':            [0x84, 0x15, 0x02, 0x01],
    'air_supply_only':        [0x84, 0x15, 0x06, 0x01, 0x00, 0x00, 0x00, 0x00, 0x10, 0x0e, 0x00, 0x00, 0x01],
    'air_extract_only':       [0x84, 0x15, 0x06, 0x01, 0x00, 0x00, 0x00, 0x00, 0x10, 0x0e, 0x00, 0x00, 0x00],
    'ventilation_balance':    [0x84, 0x15, 0x06, 0x01],
    'temp_profile_normal':    [0x84, 0x15, 0x03, 0x01, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x00],
    'temp_profile_cool':      [0x84, 0x15, 0x03, 0x01, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x01],
    'temp_profile_warm':      [0x84, 0x15, 0x03, 0x01, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x02],
    'boost_10_min':           [0x84, 0x15, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x58, 0x02, 0x00, 0x00, 0x03],
    'boost_20_min':           [0x84, 0x15, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0xB0, 0x04, 0x00, 0x00, 0x03],
    'boost_30_min':           [0x84, 0x15, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x08, 0x07, 0x00, 0x00, 0x03],
    'boost_60_min':           [0x84, 0x15, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x10, 0x0E, 0x00, 0x00, 0x03],
    'boost_end':              [0x85, 0x15, 0x01, 0x06],
    'auto':                   [0x85, 0x15, 0x08, 0x01],
    'manual':                 [0x84, 0x15, 0x08, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01],
    'test':                   [0x84, 0x15, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x58, 0x02, 0x00, 0x00, 0x03], #away
}

data = {
  0x41000400: { #16
      "name": "away_indicator",
      "ok" : True,
      "unit": "",
      "icon": "mdi:m³home-export-outline",
      "transformation": transform_away
  }, 
  0x41400400: { #17
      "name": "z_unknown_NwoNode",
      "ok" : False,
      "unit": "",
      "transformation": transform_any
  },
  0x41800400: { #18
      "name": "z_unknown_NwoNode",
      "ok" : False,
      "unit": "",
      "transformation": transform_any
  },
  0x41400c00: { #49
      "name": "operating_mode",
      "ok" : True,
      "unit": "",
      "icon": "mdi:m³brightness-auto",
      "transformation": transform_operating_mode
  },
  0x41000e00: { #56
      "name": "operating_mode2",
      "ok" : True,
      "unit": "",
      "icon": "mdi:m³brightness-auto",
      "transformation": transform_operating_mode2
  },
  0x41401000: { #65
      "name": "ventilation_level",
      "ok" : True,
      "unit": "",
      "icon": "mdi:fan",
      "transformation": lambda x: int(x[0])
  },
  0x41801000: { #66
      "name": "bypass_state",
      "ok" : True,
      "unit": "",
      "icon": "mdi:m³gate-open", 
      "transformation": lambda x: ['auto', 'open', 'close'][int(x[0])]
  },
  0x41c01000: { #67
      "name": "temperature_profile",
      "ok" : True,
      "unit": "", 
      "icon": "mdi:thermometer-lines",
      "transformation": lambda x: ['normal', 'cold', 'warm'][int(x[0])]
  },
  0x41401400: { #81
      "name": "timer_1",
      "ok" : True,
      "unit": "s",
      "transformation": transform_any
  },
  0x41801400: { #82
      "name": "timer_2",
      "ok" : True,
      "unit": "s",
      "transformation": transform_any
  },
  0x41C01400: { #83
      "name": "timer_3",
      "ok" : True,
      "unit": "s",
      "transformation": transform_any
  },
  0x41001500: { #84
      "name": "timer_4",
      "ok" : True,
      "unit": "s",
      "transformation": transform_any
  },
  0x41401500: { #85
      "name": "timer_5",
      "ok" : True,
      "unit": "s",
      "transformation": transform_any
  },
  0x41801500: { #86
      "name": "timer_6",
      "ok" : True,
      "unit": "s",
      "transformation": transform_any
  },
  0x41C01500: { #87
      "name": "timer_7",
      "ok" : True,
      "unit": "s",
      "transformation": transform_any
  },
  0x41001600: { #88
      "name": "timer_8",
      "ok" : True,
      "unit": "s",
      "transformation": transform_any
  },
  0x41001800: { #96
      "name": "bypass ??? ValveMsg",
      "ok" : False,
      "unit": "unknown",
      "transformation": transform_any
  },
  0x41401800: { #97
      "name": "bypass_b_status",
      "ok" : True,
      "icon": "mdi:gate-open",
      "unit": "",
      "transformation": transform_air_volume
  },
  0x41801800: { #98
      "name": "bypass_a_status",
      "ok" : True,
      "icon": "mdi:gate-open", 
      "unit": "",
      "transformation": transform_air_volume
  },
  0x41c01c00: { #115
      "name": "fan_exhaust_enabled",
      "ok" : True,
      "unit": "",
      "icon": "mdi:fan-chevron-down",
      "transformation": transform_any
  },
  0x41001d00: { #116
      "name": "fan_supply_enabled",
      "ok" : True,
      "unit": "",
      "icon": "mdi:fan-chevron-up",
      "transformation": transform_any
  },
  0x41401d00: { #117
      "name": "fan_exhaust_duty",
      "ok" : True,
      "unit": "%",
      "icon": "mdi:fan-chevron-down",
      "transformation": lambda x: float(x[0])
  },
  0x41801d00: { #118
      "name": "fan_supply_duty",
      "ok" : True,
      "unit": "%",
      "icon": "mdi:fan-chevron-up",
      "transformation": lambda x: float(x[0])
  },
  0x41c01d00: { #119
      "name": "fan_exhaust_flow",
      "ok" : True,
      "unit": "m³",
      "icon": "mdi:fan",
      "transformation": transform_air_volume
  },
  0x41001e00: { #120
      "name": "fan_supply_flow",
      "ok" : True,
      "unit": "m³",
      "icon": "mdi:fan",
      "transformation": transform_air_volume
  },
  0x41401e00: { #121
      "name": "fan_exhaust_speed",
      "ok" : True,
      "unit": "rpm",
      "icon": "mdi:speedometer",
      "transformation": transform_air_volume
  },
  0x41801e00: { #122
      "name": "fan_supply_speed",
      "ok" : True,
      "unit": "rpm",
      "icon": "mdi:speedometer",
      "transformation": transform_air_volume
  },
  0x41002000: { #128
      "name": "power_consumption_ventilation",
      "ok" : True,
      "unit": "W",
      "icon": "mdi:power-socket-eu",
      "transformation": lambda x: float(x[0])
  },
  0x41402000: { #129
      "name": "power_consumption_year_to_date",
      "ok" : True,
      "unit": "kWh",
      "mdi": "mdi:power-plug",
      "transformation": transform_air_volume
  },
  0x41802000: { #130
      "name": "power_consumption_total_from_start",
      "ok" : True,
      "unit": "kWh",
      "mdi": "mdi:power-plug",
      "transformation": transform_air_volume
  },
  0x41002400: { #144
      "name": "power_consumption_preheater_year_to_date",
      "ok" : True,
      "unit": "kWh",
      "mdi": "mdi:power-plug",
      "transformation": transform_any
  },
  0x41402400: { #145
      "name": "power_consumption_preheater_from_start",
      "ok" : True,
      "unit": "kWh",
      "mdi": "mdi:power-plug",
      "transformation": transform_any
  },
  0x41802400: { #146
      "name": "power_consumption_preheater_current",
      "ok" : True,
      "unit": "W",
      "mdi": "mdi:power-plug",
      "transformation": transform_any
  },
  0x41003000: { #192
      "name": "days_until_next_filter_change",
      "ok" : True,
      "unit": "days",
      "mdi": "mdi:air-filter",
      "transformation": transform_any
  },
  0x41003400: { #208
      "name": "z_Unknown_TempHumConf",
      "ok" : False,
      "unit": "",
      "transformation": transform_any
  },
  0x41403400: { #209
      "name" : "rmot",
      "ok" : True,
      "unit":"°C",
      "icon": "mdi:thermometer-alert",
      "transformation":transform_temperature
  },
  0x41803400: { #210
      "name": "z_Unknown_TempHumConf",
      "ok" : False,
      "unit": "",
      "transformation": transform_any
  },
  0x41C03400: { #211
      "name": "z_Unknown_TempHumConf",
      "ok" : False,
      "unit": "",
      "transformation": transform_any
  },
  0x41003500: { #212
      "name": "target_temperature",
      "ok" : True,
      "unit": "°C",
      "icon": "mdi:thermometer-lines",
      "transformation": transform_temperature
  },
  0x41403500: { #213
      "name": "power_avoided_heating_actual",
      "ok" : True,
      "unit": "W",
      "icon": "mdi:power-plug-off-outline",
      "transformation": transform_any
  },
  0x41803500: { #214
      "name": "power_avoided_heating_year_to_date",
      "ok" : True,
      "unit": "kWh",
      "icon": "mdi:power-plug-off-outline",
      "transformation": transform_air_volume
  },
  0x41C03500: { #215
      "name": "power_avoided_heating_from_start",
      "ok" : True,
      "unit": "kWh",
      "icon": "mdi:power-plug-off-outline",
      "transformation": transform_air_volume
  },
  0x41003600: { #216
      "name": "power_avoided_cooling_actual",
      "ok" : True,
      "unit": "W",
      "icon": "mdi:power-plug-off-outline",
      "transformation": transform_any
  },
  0x41403600: { #217
      "name": "power_avoided_cooling_year_to_date",
      "ok" : True,
      "unit": "kWh",
      "icon": "mdi:power-plug-off-outline",
      "transformation": transform_air_volume
  },
  0x41803600: { #218
      "name": "power_avoided_cooling_from_start",
      "ok" : True,
      "unit": "kWh",
      "icon": "mdi:power-plug-off-outline",
      "transformation": transform_air_volume
  },
  0x41C03600: { #219
      "name": "power_preheater_target",
      "ok" : True,
      "unit": "W",
      "icon": "mdi:power-plug",
      "transformation": transform_any
  },
  0x41003700: { #220
      "name": "air_supply_temperature_before_preheater",
      "ok" : True,
      "unit": "°C",
      "icon": "mdi:thermometer",
      "transformation": transform_temperature
  },
  0x41403700: { #221
      "name": "air_supply_temperature",
      "ok" : True,
      "unit": "°C",
      "icon": "mdi:thermometer",
      "transformation": transform_temperature
  },
  0x41803700: { #222
      "name": "z_Unknown_TempHumConf",
      "unit": "",
      "transformation": transform_any
  },
  0x41003800: { #224
      "name": "z_Unknown_VentConf",
      "unit": "",
      "transformation": transform_any
  },
  0x41403800: { #225
      "name": "z_Unknown_VentConf",
      "unit": "",
      "transformation": transform_any
  },
  0x41803800: { #226
      "name": "z_Unknown_VentConf",
      "unit": "",
      "transformation": transform_any
  },
  0x41C03800: { #227
      "name": "bypass_open_percentage",
      "ok" : True,
      "unit": "%",
      "transformation": lambda x: float(x[0])
  },
  0x41003900: { #228
      "name": "frost_disbalance",
      "ok" : True,
      "unit": "%",
      "transformation": lambda x: float(x[0])
  },
  0x41403900: { #229
      "name": "z_Unknown_VentConf",
      "unit": "",
      "transformation": transform_any
  },
  0x41803900: { #230
      "name": "z_Unknown_VentConf",
      "unit": "",
      "transformation": transform_any
  },

  0x41004000: { #256
      "name": "z_Unknown_NodeConf",
      "unit": "unknown",
      "transformation": transform_any
  },
  0x41404000: { #257 #0xe241401e
      "name": "z_Unknown_NodeConf",
      "unit": "unknown",
      "transformation": transform_any
  },

  0x41404400: { #273
      "name": "temperature_unknown",
      "unit": "°C",
      "ok": False,
      "transformation": transform_temperature
  },
  0x41804400: { #274
      "name": "air_extract_temperature",
      "ok" : True,
      "unit": "°C",
      "icon": "mdi:home-thermometer-outline",
      "transformation": transform_temperature
  },
  0x41c04400: { #275
      "name": "air_exhaust_temperature",
      "ok" : True,
      "unit": "°C",
      "icon": "mdi:home-thermometer-outline",
      "transformation": transform_temperature
  },
  0x41004500: { #276
      "name": "air_outdoor_temperature_before_preheater",
      "ok" : True,
      "unit": "°C",
      "icon": "mdi:thermometer",
      "transformation": transform_temperature
  },
  0x41404500: { #277
      "name": "air_outdoor_temperature",
      "ok" : True,
      "unit": "°C",
      "icon": "mdi:thermometer",
      "transformation": transform_temperature
  },
  0x41804500: { #278
      "name": "air_supply_temperature_2",
      "ok" : True,
      "unit": "°C",
      "icon": "mdi:thermometer",
      "transformation": transform_temperature
  },
  0x41404800: { #289
      "name": "z_unknown_HumSens",
      "unit": "",
      "transformation": transform_any
  },
  0x41804800: { #290
      "name": "air_extract_humidity",
      "ok" : True,
      "unit": "%",
      "icon": "mdi:water-percent",
      "transformation": lambda x: float(x[0])
  },
  0x41c04800: { #291
      "name": "air_exhaust_humidity", 
      "ok" : True,
      "unit": "%",
      "icon": "mdi:water-percent",
      "transformation": lambda x: float(x[0]) 
  }, 
  0x41004900: { #292
      "name": "air_outdoor_humidity_before_preheater",
      "ok" : True,
      "unit": "%",
      "icon": "mdi:water-percent",
      "transformation": lambda x: float(x[0])
  },
  0x41404900: { #293
      "name": "air_outdoor_humidity",
      "ok" : True,
      "unit": "%",
      "icon": "mdi:water-percent",
      "transformation": lambda x: float(x[0])
  },
  0x41804900: { #294
      "name": "air_supply_humidity",
      "ok" : True,
      "unit": "%",
      "icon": "mdi:water-percent",
      "transformation": lambda x: float(x[0])
  },
  0x41404c00: { #305
      "name": "pressure_exhaust",
      "ok" : True,
      "unit": "Pa",
      "icon": "mdi:package-down",
      "transformation": transform_any
  },
  0x41804c00: { #306
      "name": "pressure_supply",
      "ok" : True,
      "unit": "Pa",
      "icon": "mdi:package-down",
      "transformation": transform_any
  },

  0x41405c00: { #369
      "name": "z_Unknown_AnalogInput",
      "unit": "V?",
      "transformation": transform_any
  },
  0x41805c00: { #370
      "name": "z_Unknown_AnalogInput",
      "unit": "V?",
      "transformation": transform_any
  },
  0x41C05c00: { #371
      "name": "z_Unknown_AnalogInput",
      "unit": "V?",
      "transformation": transform_any
  },
  0x41005d00: { #372
      "name": "z_Unknown_AnalogInput",
      "unit": "V?",
      "transformation": transform_any
  },
  0x41006400: { #400
      "name": "z_Unknown_PostHeater_ActualPower",
      "unit": "W",
      "transformation": transform_any
  },
  0x41406400: { #401
      "name": "z_Unknown_PostHeater_ThisYear",
      "unit": "kWh",
      "transformation": transform_any
  },
  0x41806400: { #402
      "name": "z_Unknown_PostHeater_Total",
      "unit": "kWh",
      "transformation": transform_any
  },
#00398041 unknown 0 0 0 0 0 0 0 0
}
