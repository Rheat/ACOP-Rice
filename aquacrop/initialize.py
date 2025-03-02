__all__ = [
    "read_clock_paramaters",
    "read_weather_inputs",
    "read_model_parameters",
    "read_irrigation_management",
    "read_field_management",
    "read_groundwater_table",
    "compute_variables",
    "compute_crop_calander",
    "calculate_HIGC",
    "calculate_HI_linear",
    "read_model_initial_conditions",
    "create_soil_profile",
]

# Cell
import numpy as np
import os
import pandas as pd
from .classes import *
import pathlib
from copy import deepcopy
import aquacrop


# Cell
def read_clock_paramaters(SimStartTime, SimEndTime, OffSeason=False):
    """
    function to read in start and end simulaiton time and return a `ClockStructClass` object

    *Arguments:*\n

    `SimStartTime` : `str`:  simulation start date

    `SimEndTime` : `str` :  simulation start date

    `OffSeason` : `bool` :  simulate off season true, false

    *Returns:*


    `ClockStruct` : `ClockStructClass` : time paramaters


    """

    # extract data and put into numpy datetime format
    SimStartTime = pd.to_datetime(SimStartTime)
    SimEndTime = pd.to_datetime(SimEndTime)

    # create object
    ClockStruct = ClockStructClass()

    # add variables
    ClockStruct.SimulationStartDate = SimStartTime
    ClockStruct.SimulationEndDate = SimEndTime

    ClockStruct.nSteps = (SimEndTime - SimStartTime).days + 1
    ClockStruct.TimeSpan = pd.date_range(freq="D", start=SimStartTime, end=SimEndTime)

    ClockStruct.StepStartTime = ClockStruct.TimeSpan[0]
    ClockStruct.StepEndTime = ClockStruct.TimeSpan[1]

    ClockStruct.SimOffSeason = OffSeason

    return ClockStruct


# Cell
def read_weather_inputs(ClockStruct, weather_df):
    """
    clip weather to start and end simulation dates

    *Arguments:*\n

    `ClockStruct` : `ClockStructClass` : time paramaters

    `weather_df` : `pd.DataFrame` :  weather data

    *Returns:*

    `weather_df` : `pd.DataFrame`: clipped weather data

    """

    # get the start and end dates of simulation
    start_date = ClockStruct.SimulationStartDate
    end_date = ClockStruct.SimulationEndDate

    assert weather_df.Date.iloc[0] <= start_date
    assert weather_df.Date.iloc[-1] >= end_date

    # remove weather data outside of simulation dates
    weather_df = weather_df[weather_df.Date >= start_date]
    weather_df = weather_df[weather_df.Date <= end_date]

    return weather_df


# Cell
def read_model_parameters(ClockStruct, Soil, Crop, weather_df):
    """
    Finalise soil and crop paramaters including planting and harvest dates
    save to new object ParamStruct


    *Arguments:*\n

    `ClockStruct` : `ClockStructClass`:  time params

    `Soil` : `SoilClass` :  soil object

    `Crop` : `CropClass` :  crop object

    `planting_dates` : `list` :  list of datetimes

    `harvest_dates` : `list` : list of datetimes

    *Returns:*

    `ClockStruct` : `ClockStructClass` : updated time paramaters

    `ParamStruct` : `ParamStructClass` :  Contains model crop and soil paramaters

    """
    # create ParamStruct object
    ParamStruct = ParamStructClass()

    Soil.fill_nan()

    # Assign Soil object to ParamStruct
    ParamStruct.Soil = Soil

    while Soil.zSoil < Crop.Zmax + 0.1:
        for i in Soil.profile.index[::-1]:
            if Soil.profile.loc[i, "dz"] < 0.25:
                Soil.profile.loc[i, "dz"] += 0.1
                Soil.fill_nan()
                break

    ###########
    # crop
    ###########

    #     if isinstance(Crop, Iterable):
    #         CropList=list(Crop)
    #     else:
    #         CropList = [Crop]

    #     # assign variables to paramstruct
    #     ParamStruct.NCrops = len(CropList)
    #     if ParamStruct.NCrops > 1:
    #         ParamStruct.SpecifiedPlantCalander = 'Y'
    #     else:
    #         ParamStruct.SpecifiedPlantCalander = 'N'

    #     # add crop list to ParamStruct
    #     ParamStruct.CropList = CropList

    ############################
    # plant and harvest times
    ############################

    #     # find planting and harvest dates
    #     # check if there is more than 1 crop or multiple plant dates in sim year
    #     if ParamStruct.SpecifiedPlantCalander == "Y":
    #         # if here than crop rotation occours during same period

    #         # create variables from dataframe
    #         PlantingDates = pd.to_datetime(planting_dates)
    #         HarvestDates = pd.to_datetime(harvest_dates)

    #         if (ParamStruct.NCrops > 1):

    #             CropChoices = [crop.Name for crop in ParamStruct.CropList]

    #         assert len(CropChoices) == len(PlantingDates) == len(HarvestDates)

    # elif ParamStruct.NCrops == 1:
    # Only one crop type considered during simulation - i.e. no rotations
    # either within or between years

    CropList = [Crop]
    ParamStruct.CropList = CropList
    ParamStruct.NCrops = 1

    # Get start and end years for full simulation
    SimStartDate = ClockStruct.SimulationStartDate
    SimEndDate = ClockStruct.SimulationEndDate

    # extract the years and months of these dates
    start_end_years = pd.DatetimeIndex([SimStartDate, SimEndDate]).year
    start_end_months = pd.DatetimeIndex([SimStartDate, SimEndDate]).month

    if Crop.HarvestDate == None:
        Crop = compute_crop_calander(Crop, ClockStruct, weather_df)
        mature = int(Crop.MaturityCD + 30)
        plant = pd.to_datetime("1990/" + Crop.PlantingDate)
        harv = plant + np.timedelta64(mature, "D")
        new_harvest_date = str(harv.month) + "/" + str(harv.day)
        Crop.HarvestDate = new_harvest_date

    # check if crop growing season runs over calander year
    # Planting and harvest dates are in days/months format so just add arbitrary year
    singleYear = pd.to_datetime("1990/" + Crop.PlantingDate) < pd.to_datetime(
        "1990/" + Crop.HarvestDate
    )
    if singleYear:
        # if normal year

        # specify the planting and harvest years as normal
        plant_years = list(range(start_end_years[0], start_end_years[1] + 1))
        harvest_years = plant_years
    else:
        # if it takes over a year then the plant year finishes 1 year before end of sim
        # and harvest year starts 1 year after sim start

        if pd.to_datetime(str(start_end_years[1] + 2) + "/" + Crop.HarvestDate) < SimEndDate:

            # specify shifted planting and harvest years
            plant_years = list(range(start_end_years[0], start_end_years[1] + 1))
            harvest_years = list(range(start_end_years[0] + 1, start_end_years[1] + 2))
        else:

            plant_years = list(range(start_end_years[0], start_end_years[1]))
            harvest_years = list(range(start_end_years[0] + 1, start_end_years[1] + 1))

    # Correct for partial first growing season (may occur when simulating
    # off-season soil water balance)
    if (
        pd.to_datetime(str(plant_years[0]) + "/" + Crop.PlantingDate)
        < ClockStruct.SimulationStartDate
    ):
        # shift everything by 1 year
        plant_years = plant_years[1:]
        harvest_years = harvest_years[1:]

    # ensure number of planting and harvest years are the same
    assert len(plant_years) == len(harvest_years)

    # create lists to hold variables
    PlantingDates = []
    HarvestDates = []
    CropChoices = []

    # save full harvest/planting dates and crop choices to lists
    for i in range(len(plant_years)):
        PlantingDates.append(str(plant_years[i]) + "/" + ParamStruct.CropList[0].PlantingDate)
        HarvestDates.append(str(harvest_years[i]) + "/" + ParamStruct.CropList[0].HarvestDate)
        CropChoices.append(ParamStruct.CropList[0].Name)

    # save crop choices
    ParamStruct.CropChoices = list(CropChoices)

    # save clock paramaters
    ClockStruct.PlantingDates = pd.to_datetime(PlantingDates)
    ClockStruct.HarvestDates = pd.to_datetime(HarvestDates)
    ClockStruct.nSeasons = len(PlantingDates)

    # Initialise growing season counter
    if pd.to_datetime(ClockStruct.StepStartTime) == ClockStruct.PlantingDates[0]:
        ClockStruct.SeasonCounter = 0
    else:
        ClockStruct.SeasonCounter = -1

    # return the FileLocations object as i have added some elements
    return ClockStruct, ParamStruct


# Cell
def read_irrigation_management(ParamStruct, IrrMngt, ClockStruct):
    """
    initilize irr mngt and turn into jit classes

    *Arguments:*\n

    `ParamStruct` : `ParamStructClass` :  Contains model crop and soil paramaters

    `IrrMngt` : `IrrMngtClass` :  irr mngt params object

    `ClockStruct` : `ClockStructClass` :  time paramaters


    *Returns:*

    `ParamStruct` : `ParamStructClass` :  updated model paramaters



    """
    # If specified, read input irrigation time-series
    if IrrMngt.IrrMethod == 3:

        df = IrrMngt.Schedule.copy()

        # change the index to the date
        df.index = pd.DatetimeIndex(df.Date)

        # create a dateframe containing the daily irrigation to
        # be applied for every day in the simulation
        df = df.reindex(ClockStruct.TimeSpan, fill_value=0).drop("Date", axis=1)

        IrrMngt.Schedule = np.array(df.values, dtype=float).flatten()

    elif IrrMngt.IrrMethod == 6:
        df=IrrMngt.TDcriteria.copy()
        IrrMngt.TDcriteria=np.array(df.values,dtype=float)
    else:

        IrrMngt.Schedule = np.zeros(len(ClockStruct.TimeSpan))
        IrrMngt.TDcriteria=np.zeros((1,3))

    IrrMngt.SMT = np.array(IrrMngt.SMT, dtype=float)

    irr_mngt_struct = IrrMngtStruct(len(ClockStruct.TimeSpan),len(IrrMngt.TDcriteria))
    for a, v in IrrMngt.__dict__.items():
        if hasattr(irr_mngt_struct, a):
            irr_mngt_struct.__setattr__(a, v)

    ParamStruct.IrrMngt = irr_mngt_struct
    ParamStruct.FallowIrrMngt = IrrMngtStruct(len(ClockStruct.TimeSpan),len(IrrMngt.TDcriteria))

    return ParamStruct


# Cell
def read_field_management(ParamStruct, FieldMngt, FallowFieldMngt):
    """
    turn field management classes into jit classes

    *Arguments:*\n

    `ParamStruct` : `ParamStructClass` :  Contains model crop and soil paramaters

    `FieldMngt` : `FieldMngtClass` :  irr mngt params object

    `FallowFieldMngt` : `FieldMngtClass` :  irr mngt params object

    *Returns:*

    `ParamStruct` : `ParamStructClass` :  updated with field management info


    """

    field_mngt_struct = FieldMngtStruct()
    for a, v in FieldMngt.__dict__.items():
        if hasattr(field_mngt_struct, a):
            field_mngt_struct.__setattr__(a, v)

    fallow_field_mngt_struct = FieldMngtStruct()
    for a, v in FallowFieldMngt.__dict__.items():
        if hasattr(fallow_field_mngt_struct, a):
            fallow_field_mngt_struct.__setattr__(a, v)

    ParamStruct.FieldMngt = field_mngt_struct
    ParamStruct.FallowFieldMngt = fallow_field_mngt_struct

    return ParamStruct


# Cell
def read_groundwater_table(ParamStruct, GwStruct, ClockStruct):
    """
    Function to read input files and initialise groundwater parameters

    *Arguments:*\n

    `ParamStruct` : `ParamStructClass` :  Contains model paramaters

    `GwStruct` : `GwClass` :  groundwater params

    `ClockStruct` : `ClockStructClass` :  time params

    *Returns:*

    `ParamStruct` : `ParamStructClass` :  updated with GW info

    """

    # assign water table value and method
    WT = GwStruct.WaterTable
    WTMethod = GwStruct.Method

    # check if water table present
    if WT == "N":
        ParamStruct.WaterTable = 0
        ParamStruct.zGW = 999 * np.ones(len(ClockStruct.TimeSpan))
        ParamStruct.zGW_dates = ClockStruct.TimeSpan
        ParamStruct.WTMethod = "None"
    elif WT == "Y":
        ParamStruct.WaterTable = 1

        df = pd.DataFrame([GwStruct.dates, GwStruct.values]).T
        df.columns = ["Date", "Depth(mm)"]

        # get date in correct format
        df.Date = pd.DatetimeIndex(df.Date)

        if len(df) == 1:

            # if only 1 watertable depth then set that value to be constant
            # accross whole simulation
            zGW = df.reindex(ClockStruct.TimeSpan, fill_value=df["Depth(mm)"].iloc[0],).drop(
                "Date", axis=1
            )["Depth(mm)"]

        elif len(df) > 1:
            # check water table method
            if WTMethod == "Constant":

                # No interpolation between dates

                # create daily depths for each simulation day
                zGW = pd.Series(
                    np.nan * np.ones(len(ClockStruct.TimeSpan)), index=ClockStruct.TimeSpan
                )

                # assign constant depth for all dates in between
                for row in range(len(df)):
                    date = df.Date.iloc[row]
                    depth = df["Depth(mm)"].iloc[row]
                    zGW.loc[zGW.index >= date] = depth
                    if row == 0:
                        zGW.loc[zGW.index <= date] = depth

            elif WTMethod == "Variable":

                # Linear interpolation between dates

                # create daily depths for each simulation day
                # fill unspecified days with NaN
                zGW = pd.Series(
                    np.nan * np.ones(len(ClockStruct.TimeSpan)), index=ClockStruct.TimeSpan
                )

                for row in range(len(df)):
                    date = df.Date.iloc[row]
                    depth = df["Depth(mm)"].iloc[row]
                    zGW.loc[date] = depth

                # Interpolate daily groundwater depths
                zGW = zGW.interpolate()

        # assign values to Paramstruct object
        ParamStruct.zGW = zGW.values
        ParamStruct.zGW_dates = zGW.index.values
        ParamStruct.WTMethod = WTMethod

    return ParamStruct


# Cell
def compute_variables(
    ParamStruct,
    weather_df,
    ClockStruct,
    acfp=pathlib.Path(os.path.abspath(aquacrop.__file__)).parent,
):
    """
    Function to compute additional variables needed to run the model eg. CO2
    Creates cropstruct jit class objects

    *Arguments:*\n

    `ParamStruct` : `ParamStructClass` :  Contains model paramaters

    `weather_df` : `pd.DataFrame` :  weather data

    `ClockStruct` : `ClockStructClass` :  time params

    `acfp` : `Path` :  path to aquacrop directory containing co2 data

    *Returns:*

    `ParamStruct` : `ParamStructClass` :  updated model params


    """

    if ParamStruct.WaterTable == 1:

        ParamStruct.Soil.add_capillary_rise_params()

    # Calculate readily evaporable water in surface layer
    if ParamStruct.Soil.AdjREW == 0:
        ParamStruct.Soil.REW = round(
            (
                1000
                * (ParamStruct.Soil.profile.th_fc.iloc[0] - ParamStruct.Soil.profile.th_dry.iloc[0])
                * ParamStruct.Soil.EvapZsurf
            ),
            2,
        )

    if ParamStruct.Soil.CalcCN == 1:
        # adjust curve number
        ksat = ParamStruct.Soil.profile.Ksat.iloc[0]
        if ksat > 864:
            ParamStruct.Soil.CN = 46
        elif ksat > 347:
            ParamStruct.Soil.CN = 61
        elif ksat > 36:
            ParamStruct.Soil.CN = 72
        elif ksat > 0:
            ParamStruct.Soil.CN = 77

        assert ksat > 0

    for i in range(ParamStruct.NCrops):

        crop = ParamStruct.CropList[i]
        # crop.calculate_additional_params()

        # Crop calander
        crop = compute_crop_calander(crop, ClockStruct, weather_df)

        # Harvest index ParamStruct.Seasonal_Crop_List[ClockStruct.SeasonCounter].Paramsgrowth coefficient
        crop = calculate_HIGC(crop)

        # Days to linear HI switch point
        if crop.CropType == 3:
            # Determine linear switch point and HIGC rate for fruit/grain crops
            crop = calculate_HI_linear(crop)
        else:
            # No linear switch for leafy vegetable or root/tiber crops
            crop.tLinSwitch = 0
            crop.dHILinear = 0.0

        ParamStruct.CropList[i] = crop

    ## Calculate WP adjustment factor for elevation in CO2 concentration ##
    # Load CO2 data
    co2Data = pd.read_csv(
        acfp / "data/MaunaLoaCO2.txt", header=1, delim_whitespace=True, names=["year", "ppm"]
    )

    # Years
    start_year, end_year = pd.DatetimeIndex(
        [ClockStruct.SimulationStartDate, ClockStruct.SimulationEndDate]
    ).year
    sim_years = np.arange(start_year, end_year + 1)

    # Interpolate data
    CO2conc = np.interp(sim_years, co2Data.year, co2Data.ppm)

    # Store data
    ParamStruct.CO2data = pd.Series(CO2conc, index=sim_years)  # maybe get rid of this

    # Get CO2 concentration for first year
    CO2conc = ParamStruct.CO2data.iloc[0]

    ParamStruct.CO2 = CO2Class()

    if ParamStruct.CO2concAdj != None:
        CO2conc = ParamStruct.CO2concAdj

    ParamStruct.CO2.CurrentConc = CO2conc

    CO2ref = ParamStruct.CO2.RefConc

    # Get CO2 weighting factor for first year
    if CO2conc <= CO2ref:
        fw = 0
    else:
        if CO2conc >= 550:
            fw = 1
        else:
            fw = 1 - ((550 - CO2conc) / (550 - CO2ref))

    # Determine adjustment for each crop in first year of simulation
    for i in range(ParamStruct.NCrops):
        crop = ParamStruct.CropList[i]
        # Determine initial adjustment
        fCO2 = (CO2conc / CO2ref) / (
            1
            + (CO2conc - CO2ref)
            * (
                (1 - fw) * crop.bsted
                + fw * ((crop.bsted * crop.fsink) + (crop.bface * (1 - crop.fsink)))
            )
        )

        # Consider crop type
        if crop.WP >= 40:
            # No correction for C4 crops
            ftype = 0
        elif crop.WP <= 20:
            # Full correction for C3 crops
            ftype = 1
        else:
            ftype = (40 - crop.WP) / (40 - 20)

        # Total adjustment
        crop.fCO2 = 1 + ftype * (fCO2 - 1)

        ParamStruct.CropList[i] = crop

    # change this later
    if ParamStruct.NCrops == 1:
        crop_list = [deepcopy(ParamStruct.CropList[0]) for i in range(len(ParamStruct.CropChoices))]
        # ParamStruct.Seasonal_Crop_List = [deepcopy(ParamStruct.CropList[0]) for i in range(len(ParamStruct.CropChoices))]

    else:
        crop_list = ParamStruct.CropList

    # add crop for out of growing season
    # ParamStruct.Fallow_Crop = deepcopy(ParamStruct.Seasonal_Crop_List[0])
    Fallow_Crop = deepcopy(crop_list[0])

    ParamStruct.Seasonal_Crop_List = []
    for crop in crop_list:
        crop_struct = CropStruct()
        for a, v in crop.__dict__.items():
            if hasattr(crop_struct, a):
                crop_struct.__setattr__(a, v)

        ParamStruct.Seasonal_Crop_List.append(crop_struct)

    fallow_struct = CropStruct()
    for a, v in Fallow_Crop.__dict__.items():
        if hasattr(fallow_struct, a):
            fallow_struct.__setattr__(a, v)

    ParamStruct.Fallow_Crop = fallow_struct

    return ParamStruct


# Cell
def compute_crop_calander(crop, ClockStruct, weather_df):
    """
    Function to compute additional parameters needed to define crop phenological calendar



    *Arguments:*\n

    `crop` : `CropClass` :  Crop object containing crop paramaters

    `ClockStruct` : `ClockStructClass` :  model time paramaters

    `weather_df`: `pandas.DataFrame` :  weather data for simulation period


    *Returns:*

    `crop` : `CropClass` : updated Crop object



    """

    if len(ClockStruct.PlantingDates) == 0:
        plant_year = pd.DatetimeIndex([ClockStruct.SimulationStartDate]).year[0]
        if (
            pd.to_datetime(str(plant_year) + "/" + crop.PlantingDate)
            < ClockStruct.SimulationStartDate
        ):
            pl_date = str(plant_year + 1) + "/" + crop.PlantingDate
        else:
            pl_date = str(plant_year) + "/" + crop.PlantingDate
    else:
        pl_date = ClockStruct.PlantingDates[0]

    # Define crop calendar mode
    Mode = crop.CalendarType

    # Calculate variables %%
    if Mode == 1:  # Growth in calendar days

        # Time from sowing to end of vegatative growth period
        if crop.Determinant == 1:
            crop.CanopyDevEndCD = round(crop.HIstartCD + (crop.FloweringCD / 2))
        else:
            crop.CanopyDevEndCD = crop.SenescenceCD

        # Time from sowing to 10% canopy cover (non-stressed conditions)
        crop.Canopy10PctCD = round(crop.EmergenceCD + (np.log(0.1 / crop.CC0) / crop.CGC_CD))

        # Time from sowing to maximum canopy cover (non-stressed conditions)
        crop.MaxCanopyCD = round(
            crop.EmergenceCD
            + (
                np.log((0.25 * crop.CCx * crop.CCx / crop.CC0) / (crop.CCx - (0.98 * crop.CCx)))
                / crop.CGC_CD
            )
        )

        # Time from sowing to end of yield formation
        crop.HIendCD = crop.HIstartCD + crop.YldFormCD

        # Duplicate calendar values (needed to minimise if statements when switching between GDD and CD runs)
        crop.Emergence = crop.EmergenceCD
        crop.Canopy10Pct = crop.Canopy10PctCD
        crop.MaxRooting = crop.MaxRootingCD
        crop.Senescence = crop.SenescenceCD
        crop.Maturity = crop.MaturityCD
        crop.MaxCanopy = crop.MaxCanopyCD
        crop.CanopyDevEnd = crop.CanopyDevEndCD
        crop.HIstart = crop.HIstartCD
        crop.HIend = crop.HIendCD
        crop.YldForm = crop.YldFormCD
        if crop.CropType == 3:
            crop.FloweringEndCD = crop.HIstartCD + crop.FloweringCD
            # crop.FloweringEndCD = crop.FloweringEnd
            # crop.FloweringCD = crop.Flowering
        else:
            crop.FloweringEnd = -999
            crop.FloweringEndCD = -999
            crop.FloweringCD = -999

        # Check if converting crop calendar to GDD mode
        if crop.SwitchGDD == 1:
            #             # Extract weather data for first growing season that crop is planted
            #             for i,n in enumerate(ParamStruct.CropChoices):
            #                 if n == crop.Name:
            #                     idx = i
            #                     break
            #                 else:
            #                     idx = -1
            #             assert idx > -1

            date_range = pd.date_range(pl_date, ClockStruct.TimeSpan[-1])
            wdf = weather_df.copy()
            wdf.index = wdf.Date
            wdf = wdf.loc[date_range]
            Tmin = wdf.MinTemp
            Tmax = wdf.MaxTemp

            # Calculate GDD's
            if crop.GDDmethod == 1:

                Tmean = (Tmax + Tmin) / 2
                Tmean = Tmean.clip(lower=crop.Tbase, upper=crop.Tupp)
                GDD = Tmean - crop.Tbase

            elif crop.GDDmethod == 2:

                Tmax = Tmax.clip(lower=crop.Tbase, upper=crop.Tupp)
                Tmin = Tmin.clip(lower=crop.Tbase, upper=crop.Tupp)
                Tmean = (Tmax + Tmin) / 2
                GDD = Tmean - crop.Tbase

            elif crop.GDDmethod == 3:

                Tmax = Tmax.clip(lower=crop.Tbase, upper=crop.Tupp)
                Tmin = Tmin.clip(upper=crop.Tupp)
                Tmean = (Tmax + Tmin) / 2
                Tmean = Tmean.clip(lower=crop.Tbase)
                GDD = Tmean - crop.Tbase

            GDDcum = np.cumsum(GDD)
            # Find GDD equivalent for each crop calendar variable
            # 1. GDD's from sowing to emergence
            crop.Emergence = GDDcum.iloc[int(crop.EmergenceCD)]
            # 2. GDD's from sowing to 10# canopy cover
            crop.Canopy10Pct = GDDcum.iloc[int(crop.Canopy10PctCD)]
            # 3. GDD's from sowing to maximum rooting
            crop.MaxRooting = GDDcum.iloc[int(crop.MaxRootingCD)]
            # 4. GDD's from sowing to maximum canopy cover
            crop.MaxCanopy = GDDcum.iloc[int(crop.MaxCanopyCD)]
            # 5. GDD's from sowing to end of vegetative growth
            crop.CanopyDevEnd = GDDcum.iloc[int(crop.CanopyDevEndCD)]
            # 6. GDD's from sowing to senescence
            crop.Senescence = GDDcum.iloc[int(crop.SenescenceCD)]
            # 7. GDD's from sowing to maturity
            crop.Maturity = GDDcum.iloc[int(crop.MaturityCD)]
            # 8. GDD's from sowing to start of yield formation
            crop.HIstart = GDDcum.iloc[int(crop.HIstartCD)]
            # 9. GDD's from sowing to start of yield formation
            crop.HIend = GDDcum.iloc[int(crop.HIendCD)]
            # 10. Duration of yield formation (GDD's)
            crop.YldForm = crop.HIend - crop.HIstart

            # 11. Duration of flowering (GDD's) - (fruit/grain crops only)
            if crop.CropType == 3:
                # GDD's from sowing to end of flowering
                crop.FloweringEnd = GDDcum.iloc[int(crop.FloweringEndCD)]
                # Duration of flowering (GDD's)
                crop.Flowering = crop.FloweringEnd - crop.HIstart

            # Convert CGC to GDD mode
            # crop.CGC_CD = crop.CGC
            crop.CGC = (
                np.log((((0.98 * crop.CCx) - crop.CCx) * crop.CC0) / (-0.25 * (crop.CCx ** 2)))
            ) / (-(crop.MaxCanopy - crop.Emergence))

            # Convert CDC to GDD mode
            # crop.CDC_CD = crop.CDC
            tCD = crop.MaturityCD - crop.SenescenceCD
            if tCD <= 0:
                tCD = 1

            CCi = crop.CCx * (1 - 0.05 * (np.exp((crop.CDC_CD / crop.CCx) * tCD) - 1))
            if CCi < 0:
                CCi = 0

            tGDD = crop.Maturity - crop.Senescence
            if tGDD <= 0:
                tGDD = 5

            crop.CDC = (crop.CCx / tGDD) * np.log(1 + ((1 - CCi / crop.CCx) / 0.05))
            # Set calendar type to GDD mode
            crop.CalendarType = 2

        else:
            crop.CDC = crop.CDC_CD
            crop.CGC = crop.CGC_CD
            

        # print(crop.__dict__)
    elif Mode == 2:
        # Growth in growing degree days
        # Time from sowing to end of vegatative growth period
        if crop.Determinant == 1:
            crop.CanopyDevEnd = round(crop.HIstart + (crop.Flowering / 2))
        else:
            crop.CanopyDevEnd = crop.Senescence

        # Time from sowing to 10# canopy cover (non-stressed conditions)
        crop.Canopy10Pct = round(crop.Emergence + (np.log(0.1 / crop.CC0) / crop.CGC))

        # Time from sowing to maximum canopy cover (non-stressed conditions)
        crop.MaxCanopy = round(
            crop.Emergence
            + (
                np.log((0.25 * crop.CCx * crop.CCx / crop.CC0) / (crop.CCx - (0.98 * crop.CCx)))
                / crop.CGC
            )
        )

        # Time from sowing to end of yield formation
        crop.HIend = crop.HIstart + crop.YldForm

        # Time from sowing to end of flowering (if fruit/grain crop)
        if crop.CropType == 3:
            crop.FloweringEnd = crop.HIstart + crop.Flowering

        # Extract weather data for first growing season that crop is planted
        #         for i,n in enumerate(ParamStruct.CropChoices):
        #             if n == crop.Name:
        #                 idx = i
        #                 break
        #             else:
        #                 idx = -1
        #         assert idx> -1
        date_range = pd.date_range(pl_date, ClockStruct.TimeSpan[-1])
        wdf = weather_df.copy()
        wdf.index = wdf.Date

        wdf = wdf.loc[date_range]
        Tmin = wdf.MinTemp
        Tmax = wdf.MaxTemp

        # Calculate GDD's
        if crop.GDDmethod == 1:

            Tmean = (Tmax + Tmin) / 2
            Tmean = Tmean.clip(lower=crop.Tbase, upper=crop.Tupp)
            GDD = Tmean - crop.Tbase

        elif crop.GDDmethod == 2:

            Tmax = Tmax.clip(lower=crop.Tbase, upper=crop.Tupp)
            Tmin = Tmin.clip(lower=crop.Tbase, upper=crop.Tupp)
            Tmean = (Tmax + Tmin) / 2
            GDD = Tmean - crop.Tbase

        elif crop.GDDmethod == 3:

            Tmax = Tmax.clip(lower=crop.Tbase, upper=crop.Tupp)
            Tmin = Tmin.clip(upper=crop.Tupp)
            Tmean = (Tmax + Tmin) / 2
            Tmean = Tmean.clip(lower=crop.Tbase)
            GDD = Tmean - crop.Tbase

        GDDcum = np.cumsum(GDD).reset_index(drop=True)

        assert (
            GDDcum.values[-1] > crop.Maturity
        ), f"not enough growing degree days in simulation ({GDDcum.values[-1]}) to reach maturity ({crop.Maturity})"

        crop.MaturityCD = (GDDcum > crop.Maturity).idxmax() + 1

        assert crop.MaturityCD < 365, "crop will take longer than 1 year to mature"

        # 1. GDD's from sowing to maximum canopy cover
        crop.MaxCanopyCD = (GDDcum > crop.MaxCanopy).idxmax() + 1
        # 2. GDD's from sowing to end of vegetative growth
        crop.CanopyDevEndCD = (GDDcum > crop.CanopyDevEnd).idxmax() + 1
        # 3. Calendar days from sowing to start of yield formation
        crop.HIstartCD = (GDDcum > crop.HIstart).idxmax() + 1
        # 4. Calendar days from sowing to end of yield formation
        crop.HIendCD = (GDDcum > crop.HIend).idxmax() + 1
        # 5. Duration of yield formation in calendar days
        crop.YldFormCD = crop.HIendCD - crop.HIstartCD
        if crop.CropType == 3:
            # 1. Calendar days from sowing to end of flowering
            FloweringEnd = (GDDcum > crop.FloweringEnd).idxmax() + 1
            # 2. Duration of flowering in calendar days
            crop.FloweringCD = FloweringEnd - crop.HIstartCD
        else:
            crop.FloweringCD = -999

    return crop


# Cell
def calculate_HIGC(crop):
    """
    Function to calculate harvest index growth coefficient

    *Arguments:*\n

    `crop` : `CropClass` :  Crop object containing crop paramaters


    *Returns:*

    `crop` : `CropClass` : updated Crop object


    """
    # Determine HIGC
    # Total yield formation days
    tHI = crop.YldFormCD
    # Iteratively estimate HIGC
    HIGC = 0.001
    HIest = 0
    while HIest <= (0.98 * crop.HI0):
        HIGC = HIGC + 0.001
        HIest = (crop.HIini * crop.HI0) / (
            crop.HIini + (crop.HI0 - crop.HIini) * np.exp(-HIGC * tHI)
        )

    if HIest >= crop.HI0:
        HIGC = HIGC - 0.001

    crop.HIGC = HIGC

    return crop


# Cell
def calculate_HI_linear(crop):

    """
    Function to calculate time to switch to linear harvest index build-up,
    and associated linear rate of build-up. Only for fruit/grain crops.

    *Arguments:*\n

    `crop` : `CropClass` :  Crop object containing crop paramaters


    *Returns:*

    `crop` : `CropClass` : updated Crop object


    """
    # Determine linear switch point
    # Initialise variables
    ti = 0
    tmax = crop.YldFormCD
    HIest = 0
    HIprev = crop.HIini
    # Iterate to find linear switch point
    while (HIest <= crop.HI0) and (ti < tmax):
        ti = ti + 1
        HInew = (crop.HIini * crop.HI0) / (
            crop.HIini + (crop.HI0 - crop.HIini) * np.exp(-crop.HIGC * ti)
        )
        HIest = HInew + (tmax - ti) * (HInew - HIprev)
        HIprev = HInew

    tSwitch = ti - 1

    # Determine linear build-up rate
    if tSwitch > 0:
        HIest = (crop.HIini * crop.HI0) / (
            crop.HIini + (crop.HI0 - crop.HIini) * np.exp(-crop.HIGC * tSwitch)
        )
    else:
        HIest = 0

    dHILin = (crop.HI0 - HIest) / (tmax - tSwitch)

    crop.tLinSwitch = tSwitch
    crop.dHILinear = dHILin

    return crop


# Cell
def read_model_initial_conditions(ParamStruct, ClockStruct, InitWC):
    """
    Function to set up initial model conditions

    *Arguments:*\n

    `ParamStruct` : `ParamStructClass` :  Contains model paramaters

    `ClockStruct` : `ClockStructClass` :  model time paramaters

    `InitWC` : `InitWCClass`:  initial water content


    *Returns:*

    `ParamStruct` : `ParamStructClass` :  updated ParamStruct object

    `InitCond` : `InitCondClass` :  containing initial model conditions/counters


    """

    ###################
    # creat initial condition class
    ###################

    InitCond = InitCondClass(len(ParamStruct.Soil.profile))

    # class_args = {key:value for key, value in InitCond_class.__dict__.items() if not key.startswith('__') and not callable(key)}
    # InitCond = InitCondStruct(**class_args)

    if ClockStruct.SeasonCounter == -1:
        InitCond.Zroot = 0.
        InitCond.CC0adj = 0.

    elif ClockStruct.SeasonCounter == 0:
        InitCond.Zroot = ParamStruct.Seasonal_Crop_List[0].Zmin
        InitCond.CC0adj = ParamStruct.Seasonal_Crop_List[0].CC0

    ##################
    # save field management
    ##################

    # Initial surface storage between any soil bunds
    if ClockStruct.SeasonCounter == -1:
        # First day of simulation is in fallow period
        if (ParamStruct.FallowFieldMngt.Bunds) and (
            float(ParamStruct.FallowFieldMngt.zBund) > 0.001
        ):
            # Get initial storage between surface bunds
            InitCond.SurfaceStorage = float(ParamStruct.FallowFieldMngt.BundWater)
            if InitCond.SurfaceStorage > float(ParamStruct.FallowFieldMngt.zBund)*1000:
                InitCond.SurfaceStorage = float(ParamStruct.FallowFieldMngt.zBund)*1000
        else:
            # No surface bunds
            InitCond.SurfaceStorage = 0

    elif ClockStruct.SeasonCounter == 0:
        # First day of simulation is in first growing season
        # Get relevant field management structure parameters
        FieldMngtTmp = ParamStruct.FieldMngt
        if (FieldMngtTmp.Bunds) and (float(FieldMngtTmp.zBund) > 0.001):
            # Get initial storage between surface bunds
            InitCond.SurfaceStorage = float(FieldMngtTmp.BundWater)
            if InitCond.SurfaceStorage > float(FieldMngtTmp.zBund)*1000:
                InitCond.SurfaceStorage = float(FieldMngtTmp.zBund)*1000
        else:
            # No surface bunds
            InitCond.SurfaceStorage = 0

    ############
    # watertable
    ############

    profile = ParamStruct.Soil.profile

    # Check for presence of groundwater table
    if ParamStruct.WaterTable == 0:  # No water table present
        # Set initial groundwater level to dummy value
        InitCond.zGW = -999
        InitCond.WTinSoil = False
        # Set adjusted field capacity to default field capacity
        InitCond.th_fc_Adj = profile.th_fc.values
    elif ParamStruct.WaterTable == 1:  # Water table is present
        # Set initial groundwater level
        InitCond.zGW = float(ParamStruct.zGW[ClockStruct.TimeStepCounter])
        # Find compartment mid-points
        zMid = profile.zMid
        # Check if water table is within modelled soil profile
        if InitCond.zGW >= 0:
            idx = zMid[zMid >= InitCond.zGW].index
            if idx.shape[0] == 0:
                InitCond.WTinSoil = False
            else:
                InitCond.WTinSoil = True
        else:
            InitCond.WTinSoil = False

        # Adjust compartment field capacity
        compi = int(len(profile)) - 1
        thfcAdj = np.zeros(compi + 1)
        while compi >= 0:
            # get soil layer of compartment
            compdf = profile.loc[compi]
            if compdf.th_fc <= 0.1:
                Xmax = 1
            else:
                if compdf.th_fc >= 0.3:
                    Xmax = 2
                else:
                    pF = 2 + 0.3 * (compdf.th_fc - 0.1) / 0.2
                    Xmax = (np.exp(pF * np.log(10))) / 100

            if (InitCond.zGW < 0) or ((InitCond.zGW - zMid.iloc[compi]) >= Xmax):
                for ii in range(compi):
                    compdfii = profile.loc[ii]
                    thfcAdj[ii] = compdfii.th_fc

                compi = -1
            else:
                if compdf.th_fc >= compdf.th_s:
                    thfcAdj[compi] = compdf.th_fc
                else:
                    if zMid.iloc[compi] >= InitCond.zGW:
                        thfcAdj[compi] = compdf.th_s
                    else:
                        dV = compdf.th_s - compdf.th_fc
                        dFC = (dV / (Xmax ** 2)) * ((zMid.iloc[compi] - (InitCond.zGW - Xmax)) ** 2)
                        thfcAdj[compi] = compdf.th_fc + dFC

                compi = compi - 1

        # Store adjusted field capacity values
        InitCond.th_fc_Adj = np.round(thfcAdj, 3)

    profile["th_fc_Adj"] = np.round(InitCond.th_fc_Adj, 3)

    # create hydrology df to group by layer instead of compartment
    ParamStruct.Soil.Hydrology = profile.groupby("Layer").mean().drop(["dz", "dzsum"], axis=1)
    ParamStruct.Soil.Hydrology["dz"] = profile.groupby("Layer").sum().dz

    ###################
    # initial water contents
    ###################

    typestr = InitWC.wc_type
    methodstr = InitWC.Method

    depth_layer = InitWC.depth_layer
    datapoints = InitWC.value

    values = np.zeros(len(datapoints))

    hydf = ParamStruct.Soil.Hydrology

    # Assign data
    if typestr == "Num":
        # Values are defined as numbers (m3/m3) so no calculation required
        depth_layer = np.array(depth_layer, dtype=float)
        values = np.array(datapoints, dtype=float)

    elif typestr == "Pct":
        # Values are defined as percentage of TAW. Extract and assign value for
        # each soil layer based on calculated/input soil hydraulic properties
        depth_layer = np.array(depth_layer, dtype=float)
        datapoints = np.array(datapoints, dtype=float)

        for ii in range(len(values)):
            if methodstr == "Depth":
                depth = depth_layer[ii]
                value = datapoints[ii]

                # Find layer at specified depth
                if depth < profile.dzsum.iloc[-1]:
                    layer = profile.query(f"{depth}<dzsum").Layer.iloc[0]
                else:
                    layer = profile.Layer.iloc[-1]

                compdf = hydf.loc[layer]

                # Calculate moisture content at specified depth
                values[ii] = compdf.th_wp + ((value / 100) * (compdf.th_fc - compdf.th_wp))
            elif methodstr == "Layer":
                # Calculate moisture content at specified layer
                layer = depth_layer[ii]
                value = datapoints[ii]

                compdf = hydf.loc[layer]

                values[ii] = compdf.th_wp + ((value / 100) * (compdf.th_fc - compdf.th_wp))

    elif typestr == "Prop":
        # Values are specified as soil hydraulic properties (SAT, FC, or WP).
        # Extract and assign value for each soil layer

        for ii in range(len(values)):
            if methodstr == "Depth":
                # Find layer at specified depth
                depth = depth_layer[ii]
                value = datapoints[ii]

                # Find layer at specified depth
                if depth < profile.dzsum.iloc[-1]:
                    layer = profile.query(f"{depth}<dzsum").Layer.iloc[0]
                else:
                    layer = profile.Layer.iloc[-1]

                compdf = hydf.loc[layer]

                # Calculate moisture content at specified depth
                if value == "SAT":
                    values[ii] = compdf.th_s
                if value == "FC":
                    values[ii] = compdf.th_fc
                if value == "WP":
                    values[ii] = compdf.th_wp

            elif methodstr == "Layer":
                # Calculate moisture content at specified layer
                layer = depth_layer[ii]
                value = datapoints[ii]

                compdf = hydf.loc[layer]

                if value == "SAT":
                    values[ii] = compdf.th_s
                if value == "FC":
                    values[ii] = compdf.th_fc
                if value == "WP":
                    values[ii] = compdf.th_wp

    # Interpolate values to all soil compartments

    thini = np.zeros(int(profile.shape[0]))
    if methodstr == "Layer":
        for ii in range(len(values)):
            layer = depth_layer[ii]
            value = values[ii]

            idx = profile.query(f"Layer=={int(layer)}").index

            thini[idx] = value

        InitCond.th = thini

    elif methodstr == "Depth":
        depths = depth_layer

        # Add zero point
        if depths[0] > 0:
            depths = np.append([0], depths)
            values = np.append([values[0]], values)

        # Add end point (bottom of soil profile)
        if depths[-1] < ParamStruct.Soil.zSoil:
            depths = np.append(depths, [ParamStruct.Soil.zSoil])
            values = np.append(values, [values[-1]])

        # Find centroids of compartments
        SoilDepths = profile.dzsum.values
        comp_top = np.append([0], SoilDepths[:-1])
        comp_bot = SoilDepths
        comp_mid = (comp_top + comp_bot) / 2
        # Interpolate initial water contents to each compartment
        thini = np.interp(comp_mid, depths, values)
        InitCond.th = thini

    # If groundwater table is present and calculating water contents based on
    # field capacity, then reset value to account for possible changes in field
    # capacity caused by capillary rise effects
    if ParamStruct.WaterTable == 1:
        if (typestr == "Prop") and (datapoints[-1] == "FC"):
            InitCond.th = InitCond.th_fc_Adj

    # If groundwater table is present in soil profile then set all water
    # contents below the water table to saturation
    if InitCond.WTinSoil == True:
        # Find compartment mid-points
        SoilDepths = profile.dzsum.values
        comp_top = np.append([0], SoilDepths[:-1])
        comp_bot = SoilDepths
        comp_mid = (comp_top + comp_bot) / 2
        idx = np.where(comp_mid >= InitCond.zGW)[0][0]
        for ii in range(idx, len(profile)):
            layeri = profile.loc[ii].Layer
            InitCond.th[ii] = hydf.th_s.loc[layeri]

    InitCond.thini = InitCond.th

    ParamStruct.Soil.profile = profile
    ParamStruct.Soil.Hydrology = hydf

    return ParamStruct, InitCond


# Cell
def create_soil_profile(ParamStruct):
    """
    funciton to create soil profile class to store soil info. Its much faster to access
    the info when its in a class compared to a dataframe

    *Arguments:*\n

    `ParamStruct` : `ParamStructClass` :  Contains model crop and soil paramaters

    *Returns:*

    `ParamStruct` : `ParamStructClass` :  updated with soil profile


    """

    Profile = SoilProfileClass(int(ParamStruct.Soil.profile.shape[0]))

    pdf = ParamStruct.Soil.profile.astype("float64")

    Profile.dz = pdf.dz.values
    Profile.dzsum = pdf.dzsum.values
    Profile.zBot = pdf.zBot.values
    Profile.zTop = pdf.zTop.values
    Profile.zMid = pdf.zMid.values

    Profile.Comp = np.int64(pdf.Comp.values)
    Profile.Layer = np.int64(pdf.Layer.values)
    # Profile.Layer_dz = pdf.Layer_dz.values
    Profile.th_wp = pdf.th_wp.values
    Profile.th_fc = pdf.th_fc.values
    Profile.th_s = pdf.th_s.values

    Profile.Ksat = pdf.Ksat.values
    Profile.Penetrability = pdf.penetrability.values
    Profile.th_dry = pdf.th_dry.values
    Profile.tau = pdf.tau.values
    Profile.th_fc_Adj = pdf.th_fc_Adj.values

    if ParamStruct.WaterTable == 1:
        Profile.aCR = pdf.aCR.values
        Profile.bCR = pdf.bCR.values
    else:
        Profile.aCR = pdf.dz.values*0.
        Profile.bCR = pdf.dz.values*0.

    # ParamStruct.Soil.Profile = Profile


    ParamStruct.Soil.Profile = SoilProfileNT(dz=Profile.dz,
                                            dzsum=Profile.dzsum,
                                            zBot=Profile.zBot,
                                            zTop=Profile.zTop,
                                            zMid=Profile.zMid,
                                            Comp=Profile.Comp,
                                            Layer=Profile.Layer,
                                            th_wp=Profile.th_wp,
                                            th_fc=Profile.th_fc,
                                            th_s=Profile.th_s,
                                            Ksat=Profile.Ksat,
                                            Penetrability=Profile.Penetrability,
                                            th_dry=Profile.th_dry,
                                            tau=Profile.tau,
                                            th_fc_Adj=Profile.th_fc_Adj,
                                            aCR=Profile.aCR,
                                            bCR=Profile.bCR,
                                            )




    return ParamStruct
