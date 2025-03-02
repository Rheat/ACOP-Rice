__all__ = [
    "ClockStructClass",
    "OutputClass",
    "ParamStructClass",
    "SoilClass",
    "CropClass",
    "IrrMngtClass",
    "IrrMngtStruct",
    "spec",
    "FieldMngtClass",
    "FieldMngtStruct",
    "spec",
    "GwClass",
    "InitWCClass",
    "CropStruct",
    "CropStructNT",
    "CropStructNT_type_sig",
    "crop_spec",
    "InitCondClass",
    "WevapClass",
    "spec",
    "SoilProfileClass",
    "spec",
    "TAWClass",
    "spec",
    "DrClass",
    "spec",
    "thRZClass",
    "thRZNT",
    "thRZNT_type_sig",
    "KswClass",
    "KswNT",
    "KswNT_type_sig",
    "Ksw_spec",
    "KstClass",
    "KstNT",
    "KstNT_type_sig",
    "Kst_spec",
    "CO2Class",
    "spec",
    "SoilProfileNT",
    "SoilProfileNT_typ_sig"
]

# Cell
import numpy as np
import pandas as pd
from numba import float64, int64, boolean, types
# from collections import namedtuple
import typing

try:
    from .crops.crop_params import crop_params
except:
    from crops.crop_params import crop_params


# Cell
class ClockStructClass:
    """
    Contains model information regarding dates and step times etc.

    Atributes:\n

    `TimeStepCounter` : `int`: Keeps track of current timestep

    `ModelTermination` : `Bool`: False unless model has finished

    `SimulationStartDate` : `np.Datetime64`: Date of simulation start

    `SimulationEndDate` : `np.Datetime64`: Date of simulation end

    `TimeStep` : `int`: time step (evaluation needed)

    `nSteps` : `int`: total number of days of simulation

    `TimeSpan` : `np.array`: all dates (np.Datetime64) that lie within the start and end dates of simulation

    `StepStartTime` : `np.Datetime64`: Date at start of timestep

    `StepEndTime` : `np.Datetime64`: Date at end of timestep

    `EvapTimeSteps` : `int`: Number of time-steps (per day) for soil evaporation calculation

    `SimOffSeason` : `str`: 'Y' if you want to simulate the off season, 'N' otherwise

    `PlantingDates` : `list-like`: list of planting dates in datetime format

    `HarvestDates` : `list-like`: list of harvest dates in datetime format

    `nSeasons` : `int`: Total number of seasons to be simulated

    `SeasonCounter` : `int`: counter to keep track of which season we are currenlty simulating


        """

    def __init__(self):

        self.TimeStepCounter = 0  # Keeps track of current timestep
        self.ModelTermination = False  # False unless model has finished
        self.SimulationStartDate = 0  # Date of simulation start
        self.SimulationEndDate = 0  # Date of simulation end
        self.TimeStep = 0  # time step (evaluaiton needed)
        self.nSteps = 0  # total number of days of simulation
        self.TimeSpan = 0  # all dates that lie within the start and end dates of simulation
        self.StepStartTime = 0  # Date at start of timestep
        self.StepEndTime = 0  # Date at start of timestep
        self.EvapTimeSteps = 20  # Number of time-steps (per day) for soil evaporation calculation
        self.SimOffSeason = "N"  # 'Y' if you want to simulate the off season, 'N' otherwise
        self.PlantingDates = []  # list of crop planting dates during simulation
        self.HarvestDates = []  # list of crop planting dates during simulation
        self.nSeasons = 0  # total number of seasons (plant and harvest)
        self.SeasonCounter = -1  # running counter of seasons


# Cell
class OutputClass:
    """
    Class to hold output data

    **Atributes**:\n

    `Water` : `pandas.DataFrame` : Water storage in soil

    `Flux` : `pandas.DataFrame` : Water flux

    `Growth` : `pandas.DataFrame` : crop growth

    `Final` : `pandas.DataFrame` : final stats

    """

    def __init__(self):

        self.Water = []
        self.Flux = []
        self.Growth = []
        self.Final = []


# Cell
class ParamStructClass:
    """
    The ParamStruct class contains the bulk of model Paramaters. In general these will not change over the course of the simulation


    **Attributes**:\n

    `Soil` : `SoilClass` : Soil object contains data and paramaters related to the soil

    `FallowFieldMngt` : `FieldMngtClass` : Object containing field management variables for the off season (fallow periods)

    `NCrops` : `int` : Number of crop types to be simulated

    `SpecifiedPlantCalander` : `str` :  Specified crop rotation calendar (Y or N)

    `CropChoices` : `list` : List of crop type names in each simulated season

    `CO2data` : `pd.Series` : CO2 data indexed by year

    `CO2` : `CO2Class` : object containing reference and current co2 concentration

    `WaterTable` : `int` : Water table present (1=yes, 0=no)

    `zGW` : `np.array` : WaterTable depth (mm) for each day of simulation

    `zGW_dates` : `np.array` : Corresponding dates to the zGW values

    `WTMethod` : `str` : 'Constant' or 'Variable'

    `CropList` : `list` : List of Crop Objects which contain paramaters for all the differnet crops used in simulations

    `python_crop_list` : `list` : List of Crop Objects, one for each season

    `python_fallow_crop` : `CropClass` : Crop object for off season

    `Seasonal_Crop_List` : `list` : List of CropStructs, one for each season (jit class objects)

    `crop_name_list` : `list` : List of crop names, one for each season

    `Fallow_Crop` : `CropStruct` : CropStruct object (jit class) for off season

    `Fallow_Crop_Name` : `str` : name of fallow crop

        """

    def __init__(self):

        # soil
        self.Soil = 0

        # field management
        self.FallowFieldMngt = 0

        # variables extracted from cropmix.txt
        self.NCrops = 0
        self.SpecifiedPlantCalander = ""
        self.RotationFilename = ""

        # calculated Co2 variables
        self.CO2data = []
        self.CO2 = 0

        # water table
        self.WaterTable = 0
        self.zGW = []
        self.zGW_dates = []
        self.WTMethod = ""

        # crops
        self.CropList = []
        self.python_crop_list = []
        self.python_fallow_crop = 0
        self.Seasonal_Crop_List = []
        self.crop_name_list = []
        self.Fallow_Crop = 0
        self.Fallow_Crop_Name = ""


# Cell
class SoilClass:
    """
    The Soil Class contains Paramaters and variables of the soil used in the simulation


    **Attributes**:\n

    `profile` : `pandas.DataFrame` : holds soil profile information

    `Profile` : `SoilProfileClass` : jit class object holdsing soil profile information

    `Hydrology` : `pandas.DataFrame`: holds soil layer hydrology informaiton

    `Comp` : `pandas.DataFrame` : holds soil compartment information

    A number of float attributes specified in the initialisation of the class

        """

    def __init__(
        self,
        soilType,
        dz=[0.1] * 12,
        AdjREW=1,
        REW=9.0,
        CalcCN=0,
        CN=61.0,
        zRes=-999,
        EvapZsurf=0.04,
        EvapZmin=0.15,
        EvapZmax=0.30,
        Kex=1.1,
        fevap=4,
        fWrelExp=0.4,
        fwcc=50,
        zCN=0.3,
        zGerm=0.3,
        AdjCN=1,
        fshape_cr=16,
        zTop=0.1,
    ):

        self.Name = soilType

        self.zSoil = sum(dz)  # Total thickness of soil profile (m)
        self.nComp = len(dz)  # Total number of soil compartments
        self.nLayer = 0  # Total number of soil layers
        self.AdjREW = AdjREW  # Adjust default value for readily evaporable water (0 = No, 1 = Yes)
        self.REW = REW  # Readily evaporable water (mm) (only used if adjusting from default value)
        self.CalcCN = CalcCN  # adjust Curve number based on Ksat
        self.CN = CN  # Curve number  (0 = No, 1 = Yes)
        self.zRes = zRes  # Depth of restrictive soil layer (set to negative value if not present)

        # Assign default program properties (should not be changed without expert knowledge)
        self.EvapZsurf = EvapZsurf  # Thickness of soil surface skin evaporation layer (m)
        self.EvapZmin = EvapZmin  # Minimum thickness of full soil surface evaporation layer (m)
        self.EvapZmax = EvapZmax  # Maximum thickness of full soil surface evaporation layer (m)
        self.Kex = Kex  # Maximum soil evaporation coefficient
        self.fevap = fevap  # Shape factor describing reduction in soil evaporation in stage 2.
        self.fWrelExp = (
            fWrelExp  # Proportional value of Wrel at which soil evaporation layer expands
        )
        self.fwcc = fwcc  # Maximum coefficient for soil evaporation reduction due to sheltering effect of withered canopy
        self.zCN = zCN  # Thickness of soil surface (m) used to calculate water content to adjust curve number
        self.zGerm = (
            zGerm  # Thickness of soil surface (m) used to calculate water content for germination
        )
        self.AdjCN = AdjCN  # Adjust curve number for antecedent moisture content (0: No, 1: Yes)
        self.fshape_cr = fshape_cr  # Capillary rise shape factor
        self.zTop = max(
            zTop, dz[0]
        )  # Thickness of soil surface layer for water stress comparisons (m)

        if soilType == "custom":
            self.create_df(dz)

        elif soilType == "Clay":
            self.CN = 77
            self.CalcCN = 0
            self.REW = 14
            self.create_df(dz)
            self.add_layer(sum(dz), 0.39, 0.54, 0.55, 35, 100)

        elif soilType == "ClayLoam":
            self.CN = 72
            self.CalcCN = 0
            self.REW = 11
            self.create_df(dz)
            self.add_layer(sum(dz), 0.23, 0.39, 0.5, 125, 100)

        elif soilType == "Loam":
            self.CN = 61
            self.CalcCN = 0
            self.REW = 9
            self.create_df(dz)
            self.add_layer(sum(dz), 0.15, 0.31, 0.46, 500, 100)

        elif soilType == "LoamySand":
            self.CN = 46
            self.CalcCN = 0
            self.REW = 5
            self.create_df(dz)
            self.add_layer(sum(dz), 0.08, 0.16, 0.38, 2200, 100)

        elif soilType == "Sand":
            self.CN = 46
            self.CalcCN = 0
            self.REW = 4
            self.create_df(dz)
            self.add_layer(sum(dz), 0.06, 0.13, 0.36, 3000, 100)

        elif soilType == "SandyClay":
            self.CN = 77
            self.CalcCN = 0
            self.REW = 10
            self.create_df(dz)
            self.add_layer(sum(dz), 0.27, 0.39, 0.5, 35, 100)

        elif soilType == "SandyClayLoam":
            self.CN = 72
            self.CalcCN = 0
            self.REW = 9
            self.create_df(dz)
            self.add_layer(sum(dz), 0.20, 0.32, 0.47, 225, 100)

        elif soilType == "SandyLoam":
            self.CN = 46
            self.CalcCN = 0
            self.REW = 7
            self.create_df(dz)
            self.add_layer(sum(dz), 0.10, 0.22, 0.41, 1200, 100)

        elif soilType == "Silt":
            self.CN = 61
            self.CalcCN = 0
            self.REW = 11
            self.create_df(dz)
            self.add_layer(sum(dz), 0.09, 0.33, 0.43, 500, 100)

        elif soilType == "SiltClayLoam":
            self.CN = 72
            self.CalcCN = 0
            self.REW = 13
            self.create_df(dz)
            self.add_layer(sum(dz), 0.23, 0.44, 0.52, 150, 100)

        elif soilType == "SiltLoam":
            self.CN = 61
            self.CalcCN = 0
            self.REW = 11
            self.create_df(dz)
            self.add_layer(sum(dz), 0.13, 0.33, 0.46, 575, 100)

        elif soilType == "SiltClay":
            self.CN = 72
            self.CalcCN = 0
            self.REW = 14
            self.create_df(dz)
            self.add_layer(sum(dz), 0.32, 0.50, 0.54, 100, 100)

        elif soilType == "Paddy":
            self.CN = 77
            self.CalcCN = 0
            self.REW = 10
            self.create_df(dz)
            self.add_layer(0.5, 0.32, 0.50, 0.54, 15, 100)
            self.add_layer(1.5, 0.39, 0.54, 0.55, 2, 100)

        elif soilType == "ac_TunisLocal":
            self.CN = 46
            self.CalcCN = 0
            self.REW = 7
            dz = [0.1] * 6 + [0.15] * 5 + [0.2]
            self.create_df(dz)
            self.add_layer(0.3, 0.24, 0.40, 0.50, 155, 100)
            self.add_layer(1.7, 0.11, 0.33, 0.46, 500, 100)

        else:
            print("wrong soil type")
            assert 1 == 2

    def __repr__(self):
        for key in self.__dict__:
            if key != "profile":
                print(f"{key}: {getattr(self,key)}")

        return " "

    def create_df(self, dz):

        self.profile = pd.DataFrame(
            np.empty((len(dz), 4)), columns=["Comp", "Layer", "dz", "dzsum"]
        )
        self.profile.dz = dz
        self.profile.dzsum = np.cumsum(self.profile.dz).round(2)
        self.profile.Comp = np.arange(len(dz))
        self.profile.Layer = np.nan

        self.profile["zBot"] = self.profile.dzsum
        self.profile["zTop"] = self.profile["zBot"] - self.profile.dz
        self.profile["zMid"] = (self.profile["zTop"] + self.profile["zBot"]) / 2

    def calculate_soil_hydraulic_properties(self, Sand, Clay, OrgMat, DF=1):

        """
        Function to calculate soil hydraulic properties, given textural inputs.
        Calculations use pedotransfer function equations described in Saxton and Rawls (2006)


        """

        # do calculations

        # Water content at permanent wilting point
        Pred_thWP = (
            -(0.024 * Sand)
            + (0.487 * Clay)
            + (0.006 * OrgMat)
            + (0.005 * Sand * OrgMat)
            - (0.013 * Clay * OrgMat)
            + (0.068 * Sand * Clay)
            + 0.031
        )

        th_wp = Pred_thWP + (0.14 * Pred_thWP) - 0.02

        # Water content at field capacity and saturation
        Pred_thFC = (
            -(0.251 * Sand)
            + (0.195 * Clay)
            + (0.011 * OrgMat)
            + (0.006 * Sand * OrgMat)
            - (0.027 * Clay * OrgMat)
            + (0.452 * Sand * Clay)
            + 0.299
        )

        PredAdj_thFC = Pred_thFC + (
            (1.283 * (np.power(Pred_thFC, 2))) - (0.374 * Pred_thFC) - 0.015
        )

        Pred_thS33 = (
            (0.278 * Sand)
            + (0.034 * Clay)
            + (0.022 * OrgMat)
            - (0.018 * Sand * OrgMat)
            - (0.027 * Clay * OrgMat)
            - (0.584 * Sand * Clay)
            + 0.078
        )

        PredAdj_thS33 = Pred_thS33 + ((0.636 * Pred_thS33) - 0.107)
        Pred_thS = (PredAdj_thFC + PredAdj_thS33) + ((-0.097 * Sand) + 0.043)

        pN = (1 - Pred_thS) * 2.65
        pDF = pN * DF
        PorosComp = (1 - (pDF / 2.65)) - (1 - (pN / 2.65))
        PorosCompOM = 1 - (pDF / 2.65)

        DensAdj_thFC = PredAdj_thFC + (0.2 * PorosComp)
        DensAdj_thS = PorosCompOM

        th_fc = DensAdj_thFC
        th_s = DensAdj_thS

        # Saturated hydraulic conductivity (mm/day)
        lmbda = 1 / ((np.log(1500) - np.log(33)) / (np.log(th_fc) - np.log(th_wp)))
        Ksat = (1930 * (th_s - th_fc) ** (3 - lmbda)) * 24

        # Water content at air dry
        th_dry = th_wp / 2

        # round values
        th_dry = round(10_000 * th_dry) / 10_000
        th_wp = round(1000 * th_wp) / 1000
        th_fc = round(1000 * th_fc) / 1000
        th_s = round(1000 * th_s) / 1000
        Ksat = round(10 * Ksat) / 10

        return th_wp, th_fc, th_s, Ksat

    def add_layer_from_texture(self, thickness, Sand, Clay, OrgMat, penetrability):

        th_wp, th_fc, th_s, Ksat = self.calculate_soil_hydraulic_properties(
            Sand / 100, Clay / 100, OrgMat
        )

        self.add_layer(thickness, th_wp, th_fc, th_s, Ksat, penetrability)

    def add_layer(self, thickness, thWP, thFC, thS, Ksat, penetrability):

        self.nLayer += 1

        num_layers = len(self.profile.dropna().Layer.unique())

        new_layer = num_layers + 1

        if new_layer == 1:
            self.profile.loc[
                (round(thickness, 2) >= round(self.profile.dzsum, 2)), "Layer"
            ] = new_layer
        else:
            last = self.profile[self.profile.Layer == new_layer - 1].dzsum.values[-1]
            self.profile.loc[
                (thickness + last >= self.profile.dzsum) & (self.profile.Layer.isna()), "Layer"
            ] = new_layer

        self.profile.loc[self.profile.Layer == new_layer, "th_dry"] = self.profile.Layer.map(
            {new_layer: thWP / 2}
        )
        self.profile.loc[self.profile.Layer == new_layer, "th_wp"] = self.profile.Layer.map(
            {new_layer: thWP}
        )
        self.profile.loc[self.profile.Layer == new_layer, "th_fc"] = self.profile.Layer.map(
            {new_layer: thFC}
        )
        self.profile.loc[self.profile.Layer == new_layer, "th_s"] = self.profile.Layer.map(
            {new_layer: thS}
        )
        self.profile.loc[self.profile.Layer == new_layer, "Ksat"] = self.profile.Layer.map(
            {new_layer: Ksat}
        )
        self.profile.loc[self.profile.Layer == new_layer, "penetrability"] = self.profile.Layer.map(
            {new_layer: penetrability}
        )

        # Calculate drainage characteristic (tau)
        # Calculations use equation given by Raes et al. 2012
        tau = round(0.0866 * (Ksat ** 0.35), 2)
        if tau > 1:
            tau = 1
        elif tau < 0:
            tau = 0

        self.profile.loc[self.profile.Layer == new_layer, "tau"] = self.profile.Layer.map(
            {new_layer: tau}
        )

    def fill_nan(self,):

        self.profile = self.profile.fillna(method="ffill")

        self.profile.dz = self.profile.dz.round(2)

        self.profile.dzsum = self.profile.dz.cumsum().round(2)

        self.zSoil = round(self.profile.dz.sum(), 2)

        self.nComp = len(self.profile)

        self.profile.Layer = self.profile.Layer.astype(int)

    def add_capillary_rise_params(self,):
        # Calculate capillary rise parameters for all soil layers
        # Only do calculation if water table is present. Calculations use equations
        # described in Raes et al. (2012)
        prof = self.profile

        hydf = prof.groupby("Layer").mean().drop(["dz", "dzsum"], axis=1)

        hydf["aCR"] = 0
        hydf["bCR"] = 0

        for layer in hydf.index.unique():
            layer = int(layer)

            soil = hydf.loc[layer]

            thwp = soil.th_wp
            thfc = soil.th_fc
            ths = soil.th_s
            Ksat = soil.Ksat

            aCR = 0
            bCR = 0

            if (
                (thwp >= 0.04)
                and (thwp <= 0.15)
                and (thfc >= 0.09)
                and (thfc <= 0.28)
                and (ths >= 0.32)
                and (ths <= 0.51)
            ):

                # Sandy soil class
                if (Ksat >= 200) and (Ksat <= 2000):
                    aCR = -0.3112 - (Ksat * (1e-5))
                    bCR = -1.4936 + (0.2416 * np.log(Ksat))
                elif Ksat < 200:
                    aCR = -0.3112 - (200 * (1e-5))
                    bCR = -1.4936 + (0.2416 * np.log(200))
                elif Ksat > 2000:
                    aCR = -0.3112 - (2000 * (1e-5))
                    bCR = -1.4936 + (0.2416 * np.log(2000))

            elif (
                (thwp >= 0.06)
                and (thwp <= 0.20)
                and (thfc >= 0.23)
                and (thfc <= 0.42)
                and (ths >= 0.42)
                and (ths <= 0.55)
            ):

                # Loamy soil class
                if (Ksat >= 100) and (Ksat <= 750):
                    aCR = -0.4986 + (9 * (1e-5) * Ksat)
                    bCR = -2.132 + (0.4778 * np.log(Ksat))
                elif Ksat < 100:
                    aCR = -0.4986 + (9 * (1e-5) * 100)
                    bCR = -2.132 + (0.4778 * np.log(100))
                elif Ksat > 750:
                    aCR = -0.4986 + (9 * (1e-5) * 750)
                    bCR = -2.132 + (0.4778 * np.log(750))

            elif (
                (thwp >= 0.16)
                and (thwp <= 0.34)
                and (thfc >= 0.25)
                and (thfc <= 0.45)
                and (ths >= 0.40)
                and (ths <= 0.53)
            ):

                # Sandy clayey soil class
                if (Ksat >= 5) and (Ksat <= 150):
                    aCR = -0.5677 - (4 * (1e-5) * Ksat)
                    bCR = -3.7189 + (0.5922 * np.log(Ksat))
                elif Ksat < 5:
                    aCR = -0.5677 - (4 * (1e-5) * 5)
                    bCR = -3.7189 + (0.5922 * np.log(5))
                elif Ksat > 150:
                    aCR = -0.5677 - (4 * (1e-5) * 150)
                    bCR = -3.7189 + (0.5922 * np.log(150))

            elif (
                (thwp >= 0.20)
                and (thwp <= 0.42)
                and (thfc >= 0.40)
                and (thfc <= 0.58)
                and (ths >= 0.49)
                and (ths <= 0.58)
            ):

                # Silty clayey soil class
                if (Ksat >= 1) and (Ksat <= 150):
                    aCR = -0.6366 + (8 * (1e-4) * Ksat)
                    bCR = -1.9165 + (0.7063 * np.log(Ksat))
                elif Ksat < 1:
                    aCR = -0.6366 + (8 * (1e-4) * 1)
                    bCR = -1.9165 + (0.7063 * np.log(1))
                elif Ksat > 150:
                    aCR = -0.6366 + (8 * (1e-4) * 150)
                    bCR = -1.9165 + (0.7063 * np.log(150))

            assert aCR != 0
            assert bCR != 0

            prof.loc[prof.Layer == layer, "aCR"] = prof.Layer.map({layer: aCR})
            prof.loc[prof.Layer == layer, "bCR"] = prof.Layer.map({layer: bCR})

        self.profile = prof


# Cell
class CropClass:
    """
    The Crop Class contains Paramaters and variables of the crop used in the simulation


    **Attributes**:\n

    `c_name`: `str`: crop name ('custom' or one of built in defaults e.g. 'Maize')

    `PlantingDate` : `str` : Planting Date (mm/dd)

    `HarvestDate` : `str` : Latest Harvest Date (mm/dd)

    `CropType` : `int` : Crop Type (1 = Leafy vegetable, 2 = Root/tuber, 3 = Fruit/grain)

    `PlantMethod` : `int` : Planting method (0 = Transplanted, 1 =  Sown)

    `CalendarType` : `int` : Calendar Type (1 = Calendar days, 2 = Growing degree days)

    `SwitchGDD` : `int` : Convert calendar to GDD mode if inputs are given in calendar days (0 = No; 1 = Yes)



    `IrrMngt`: `dict` :  dictionary containting irrigation management information

    `IrrSchd` : `pandas.DataFrame` :  pandas DataFrame containing the Irrigation Schedule if predefined

    `FieldMngt` : `dict` :   Dictionary containing field management variables for the growing season of the crop

     A number of default program properties of type float are also specified during initialisation

    """

    def __init__(self, c_name, PlantingDate, HarvestDate=None, **kwargs):

        self.Name = c_name

        # Assign default program properties (should not be changed without expert knowledge)

        self.fshape_b = 13.8135  # Shape factor describing the reduction in biomass production for insufficient growing degree days
        self.PctZmin = 70  # Initial percentage of minimum effective rooting depth
        self.fshape_ex = -6  # Shape factor describing the effects of water stress on root expansion
        self.ETadj = (
            1  # Adjustment to water stress thresholds depending on daily ET0 (0 = No, 1 = Yes)
        )
        self.Aer = (
            5  # Vol (%) below saturation at which stress begins to occur due to deficient aeration
        )
        self.LagAer = 3  # Number of days lag before aeration stress affects crop growth
        self.beta = 12  # Reduction (%) to p_lo3 when early canopy senescence is triggered
        self.a_Tr = 1  # Exponent parameter for adjustment of Kcx once senescence is triggered
        self.GermThr = 0.2  # Proportion of total water storage needed for crop to germinate
        self.CCmin = 0.05  # Minimum canopy size below which yield formation cannot occur
        self.MaxFlowPct = (
            100 / 3
        )  # Proportion of total flowering time (%) at which peak flowering occurs
        self.HIini = 0.01  # Initial harvest index
        self.bsted = 0.000138  # WP co2 adjustment parameter given by Steduto et al. 2007
        self.bface = 0.001165  # WP co2 adjustment parameter given by FACE experiments

        if c_name == "custom":

            self.Name = "custom"
            self.PlantingDate = PlantingDate  # Planting Date (mm/dd)
            self.HarvestDate = HarvestDate  # Latest Harvest Date (mm/dd)

        
        elif c_name in crop_params.keys():
            self.__dict__.update((k, v) for k, v in crop_params[c_name].items())
            self.PlantingDate = PlantingDate  # Planting Date (mm/dd)
            self.HarvestDate = HarvestDate  # Latest Harvest Date (mm/dd)

        else:
            assert c_name in crop_params.keys(), f"Crop name not defined in crop_params dictionary, \
        if defining a custom crop please use crop name 'custom'. Otherwise use one of the \
        pre-defined crops: {crop_params.keys()}"

        # overide any pre-defined paramater with any passed by the user
        allowed_keys = {
            "fshape_b",
            "PctZmin",
            "fshape_ex",
            "ETadj",
            "Aer",
            "LagAer",
            "beta",
            "a_Tr",
            "GermThr",
            "CCmin",
            "MaxFlowPct",
            "HIini",
            "bsted",
            "bface",
            "Name",
            "CropType",
            "PlantMethod",
            "CalendarType",
            "SwitchGDD",
            "PlantingDate",
            "HarvestDate",
            "Emergence",
            "MaxRooting",
            "Senescence",
            "Maturity",
            "HIstart",
            "Flowering",
            "YldForm",            
            "GDDmethod",
            "Tbase",
            "Tupp",
            "PolHeatStress",
            "Tmax_up",
            "Tmax_lo",
            "PolColdStress",
            "Tmin_up",
            "Tmin_lo",
            "TrColdStress",
            "GDD_up",
            "GDD_lo",
            "Zmin",
            "Zmax",
            "fshape_r",
            "SxTopQ",
            "SxBotQ",
            "SeedSize",
            "PlantPop",
            "CCx",
            "CDC",
            "CGC",
            "Kcb",
            "fage",
            "WP",
            "WPy",
            "fsink",
            "HI0",
            "dHI_pre",
            "a_HI",
            "b_HI",
            "dHI0",
            "Determinant",
            "exc",
            "p_up1",
            "p_up2",
            "p_up3",
            "p_up4",
            "p_lo1",
            "p_lo2",
            "p_lo3",
            "p_lo4",
            "fshape_w1",
            "fshape_w2",
            "fshape_w3",
            "fshape_w4",
            "CGC_CD",
            "CDC_CD",
            "EmergenceCD",
            "MaxRootingCD",
            "SenescenceCD",
            "MaturityCD",
            "HIstartCD",
            "FloweringCD",
            "YldFormCD",

        }

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)

        self.calculate_additional_params()

    def calculate_additional_params(self,):

        # Calculate additional parameters for all self types in mix

        # Fractional canopy cover size at emergence
        self.CC0 = self.PlantPop * self.SeedSize * 1e-8
        # Root extraction terms
        SxTopQ = self.SxTopQ
        SxBotQ = self.SxBotQ
        S1 = self.SxTopQ
        S2 = self.SxBotQ
        if S1 == S2:
            SxTop = S1
            SxBot = S2
        else:
            if SxTopQ < SxBotQ:
                S1 = SxBotQ
                S2 = SxTopQ

            xx = 3 * (S2 / (S1 - S2))
            if xx < 0.5:
                SS1 = (4 / 3.5) * S1
                SS2 = 0
            else:
                SS1 = (xx + 3.5) * (S1 / (xx + 3))
                SS2 = (xx - 0.5) * (S2 / xx)

            if SxTopQ > SxBotQ:
                SxTop = SS1
                SxBot = SS2
            else:
                SxTop = SS2
                SxBot = SS1

        self.SxTop = SxTop
        self.SxBot = SxBot

        # Water stress thresholds
        self.p_up = np.array([self.p_up1, self.p_up2, self.p_up3, self.p_up4])

        self.p_lo = np.array([self.p_lo1, self.p_lo2, self.p_lo3, self.p_lo4])

        self.fshape_w = np.array([self.fshape_w1, self.fshape_w2, self.fshape_w3, self.fshape_w4])


#     def flowerfun(self,xx):
#         assert self.CropType == 3
#         return (0.00558*(xx**0.63))-(0.000969*xx)-0.00383


# Cell
class IrrMngtClass:

    """
    Farmer Class defines irrigation strategy

    **Attributes:**\n


    `Name` : `str` :  name

    `IrrMethod` : `int` :  Irrigation method {0: rainfed, 1: soil moisture targets, 2: set time interval,
                                              3: predifined schedule, 4: net irrigation, 5: constant depth }

    `WetSurf` : `int` : Soil surface wetted by irrigation (%)

    `AppEff` : `int` : Irrigation application efficiency (%)

    `MaxIrr` : `float` : Maximum depth (mm) that can be applied each day

    `SMT` : `list` :  Soil moisture targets (%TAW) to maintain in each growth stage (only used if irrigation method is equal to 1)

    `IrrInterval` : `int` : Irrigation interval in days (only used if irrigation method is equal to 2)

    `Schedule` : `pandas.DataFrame` : DataFrame containing dates and depths

    `NetIrrSMT` : `float` : Net irrigation threshold moisture level (% of TAW that will be maintained, for IrrMethod=4)

    `Depth` : `float` : constant depth to apply on each day
    
    'TDcriteria' : 'pandas.DataFrame' : DataFrame containing time and depth criteria

    """

    def __init__(self, IrrMethod, **kwargs):
        self.IrrMethod = IrrMethod

        self.WetSurf = 100.0
        self.AppEff = 100.0
        self.MaxIrr = 25.0
        self.MaxIrrSeason = 10_000.0
        self.SMT = np.zeros(4)
        self.IrrInterval = 0
        self.Schedule = []
        self.TDcriteria=np.zeros((1,3))
        self.NetIrrSMT = 80.0
        self.depth = 0.0

        if IrrMethod == 1:
            self.SMT = [100] * 4

        if IrrMethod == 2:
            self.IrrInterval = 3

        if IrrMethod == 3:
            # wants a pandas dataframe with Date and Depth, pd.Datetime and float
            """
            dates = pd.DatetimeIndex(['20/10/1979','20/11/1979','20/12/1979'])
            depths = [25,25,25]
            irr=pd.DataFrame([dates,depths]).T
            irr.columns=['Date','Depth']
            """
            self.Schedule = pd.DataFrame(columns=["Date", "Depth"])

        if IrrMethod == 4:
            self.NetIrrSMT = 80

        if IrrMethod == 5:
            self.depth = 0
        if IrrMethod == 6:
            #wants a pandas dataframe with Day after plant,Minimum and Depth, pd.Datetime and float
            self.MaxIrr = 150.
            '''
            T_Criteria = [1,8,62,72]
            Minimum=[10,20,10,0]
            depths = [20,30,40,0]          
            self.TDcriteria =pd.DataFrame([T_Criteria,Minimum,depths]).T
            self.TDcriteria.columns=['T_Criteria','Minimum','Depth']
            '''
        
        allowed_keys = {
            "name",
            "WetSurf",
            "AppEff",
            "MaxIrr",
            "MaxIrrSeason",
            "SMT",
            "IrrInterval",
            "NetIrrSMT",
            "Schedule",
            "depth",
            "TDcriteria",
        }

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)


# Cell
spec = [
    ("IrrMethod", int64),
    ("WetSurf", float64),
    ("AppEff", float64),
    ("MaxIrr", float64),
    ("MaxIrrSeason", float64),
    ("SMT", float64[:]),
    ("IrrInterval", int64),
    ("Schedule", float64[:]),
    ("NetIrrSMT", float64),
    ("depth", float64),
    ('TDcriteria', float64[:,:]),
]


#@jitclass(spec)
class IrrMngtStruct:

    """


    """

    def __init__(self, sim_len):
        self.IrrMethod = 0

        self.WetSurf = 100.0
        self.AppEff = 100.0
        self.MaxIrr = 25.0
        self.MaxIrrSeason = 10_000
        self.SMT = np.zeros(4)
        self.IrrInterval = 0
        self.Schedule = np.zeros(sim_len)
        self.NetIrrSMT = 80.0
        self.depth = 0.0
        self.TDcriteria=np.zeros((cri_len,3))

# Cell
class FieldMngtClass:
    """
    Field Management Class

    **Attributes:**\n


    `Mulches` : `bool` :  Soil surface covered by mulches (Y or N)

    `Bunds` : `bool` :  Surface bunds present (Y or N)

    `CNadj` : `bool` : Field conditions affect curve number (Y or N)

    `SRinhb` : `bool` : Management practices fully inhibit surface runoff (Y or N)



    `MulchPct` : `float` :  Area of soil surface covered by mulches (%)

    `fMulch` : `float` : Soil evaporation adjustment factor due to effect of mulches

    `zBund` : `pandas.DataFrame` : DataFrame containing dates and Bund height(m)

    `BundWater` : `float` : Initial water height in surface bunds (mm)

    `CNadjPct` : `float` : Percentage change in curve number (positive or negative)

    """

    def __init__(
        self,
        Mulches=False,
        Bunds=False,
        CNadj=False,
        SRinhb=False,
        MulchPct=50,
        fMulch=0.5,
        zBund=0,
        BundWater=0,
        CNadjPct=0,
    ):

        self.Mulches = Mulches  #  Soil surface covered by mulches (Y or N)
        self.Bunds = Bunds  #  Surface bunds present (Y or N)
        self.CNadj = CNadj  # Field conditions affect curve number (Y or N)
        self.SRinhb = SRinhb  # Management practices fully inhibit surface runoff (Y or N)

        self.MulchPct = MulchPct  #  Area of soil surface covered by mulches (%)
        self.fMulch = fMulch  # Soil evaporation adjustment factor due to effect of mulches
        self.zBund = np.array(zBund) # Bund height (m)
        self.BundWater = BundWater  # Initial water height in surface bunds (mm)
        self.CNadjPct = CNadjPct  # Percentage change in curve number (positive or negative)


# Cell
spec = [
    ("Mulches", boolean),
    ("Bunds", boolean),
    ("CNadj", boolean),
    ("SRinhb", boolean),
    ("MulchPct", float64),
    ("fMulch", float64),
    ("zBund", float64[:,:]),
    ("BundWater", float64),
    ("CNadjPct", float64),
]


#@jitclass(spec)
class FieldMngtStruct:

    """


    """

    def __init__(self):
        self.Mulches = False
        self.Bunds = False
        self.CNadj = False
        self.SRinhb = False

        self.MulchPct = 0.0
        self.fMulch = 0.0
        self.zBund = np.zeros((2,1))
        self.BundWater = 0.0
        self.CNadjPct = 0.0


# Cell
class GwClass:
    """
    Ground Water Class stores information on water table params

    **Attributes:**\n


    `WaterTable` : `str` :  Water table considered (Y or N)

    `Method` : `str` :  Water table input data ('Constant' or 'Variable')

    `dates` : `list` : water table observation dates

    `values` : `list` : water table observation depths

    """

    def __init__(self, WaterTable="N", Method="Constant", dates=[], values=[]):

        self.WaterTable = WaterTable
        self.Method = Method
        self.dates = dates
        self.values = values


# Cell
class InitWCClass:
    """
    Initial water content Class defines water content at start of sim

    **Attributes:**\n

    `wc_type` : `str` :  Type of value ('Prop' = 'WP'/'FC'/'SAT'; 'Num' = XXX m3/m3; 'Pct' = % TAW))

    `Method` : `str` :  Method ('Depth' = Interpolate depth points; 'Layer' = Constant value for each soil layer)

    `depth_layer` : `list` : location in soil profile (soil layer or depth)

    `value` : `list` : value at that location

    """

    def __init__(self, wc_type="Prop", Method="Layer", depth_layer=[1], value=["FC"]):

        assert len(depth_layer) == len(value)

        self.wc_type = wc_type
        self.Method = Method
        self.depth_layer = depth_layer
        self.value = value


# Cell
crop_spec = [
    ("fshape_b", float64),
    ("PctZmin", float64),
    ("fshape_ex", float64),
    ("ETadj", float64),
    ("Aer", float64),
    ("LagAer", int64),
    ("beta", float64),
    ("a_Tr", float64),
    ("GermThr", float64),
    ("CCmin", float64),
    ("MaxFlowPct", float64),
    ("HIini", float64),
    ("bsted", float64),
    ("bface", float64),
    ("CropType", int64),
    ("PlantMethod", int64),
    ("CalendarType", int64),
    ("SwitchGDD", int64),
    ("EmergenceCD", int64),
    ("Canopy10PctCD", int64),
    ("MaxRootingCD", int64),
    ("SenescenceCD", int64),
    ("MaturityCD", int64),
    ("MaxCanopyCD", int64),
    ("CanopyDevEndCD", int64),
    ("HIstartCD", int64),
    ("HIendCD", int64),
    ("YldFormCD", int64),
    ("Emergence", float64),
    ("MaxRooting", float64),
    ("Senescence", float64),
    ("Maturity", float64),
    ("HIstart", float64),
    ("Flowering", float64),
    ("YldForm", float64),
    ("HIend", float64),
    ("CanopyDevEnd", float64),
    ("MaxCanopy", float64),
    ("GDDmethod", int64),
    ("Tbase", float64),
    ("Tupp", float64),
    ("PolHeatStress", int64),
    ("Tmax_up", float64),
    ("Tmax_lo", float64),
    ("PolColdStress", int64),
    ("Tmin_up", float64),
    ("Tmin_lo", float64),
    ("TrColdStress", int64),
    ("GDD_up", float64),
    ("GDD_lo", float64),
    ("Zmin", float64),
    ("Zmax", float64),
    ("fshape_r", float64),
    ("SxTopQ", float64),
    ("SxBotQ", float64),
    ("SxTop", float64),
    ("SxBot", float64),
    ("SeedSize", float64),
    ("PlantPop", int64),
    ("CCx", float64),
    ("CDC", float64),
    ("CGC", float64),
    ("CDC_CD", float64),
    ("CGC_CD", float64),
    ("Kcb", float64),
    ("fage", float64),
    ("WP", float64),
    ("WPy", float64),
    ("fsink", float64),
    ("HI0", float64),
    ("dHI_pre", float64),
    ("a_HI", float64),
    ("b_HI", float64),
    ("dHI0", float64),
    ("Determinant", int64),
    ("exc", float64),
    ("p_up", float64[:]),
    ("p_lo", float64[:]),
    ("fshape_w", float64[:]),
    ("Canopy10Pct", int64),
    ("CC0", float64),
    ("HIGC", float64),
    ("tLinSwitch", int64),
    ("dHILinear", float64),
    ("fCO2", float64),
    ("FloweringCD", int64),
    ("FloweringEnd", float64),
]


#@jitclass(spec)
class CropStruct(object):
    """
    The Crop Class contains Paramaters and variables of the crop used in the simulation


    **Attributes**:\n



    """

    def __init__(self,):

        # Assign default program properties (should not be changed without expert knowledge)

        self.fshape_b = 13.8135  # Shape factor describing the reduction in biomass production for insufficient growing degree days
        self.PctZmin = 70  # Initial percentage of minimum effective rooting depth
        self.fshape_ex = -6  # Shape factor describing the effects of water stress on root expansion
        self.ETadj = (
            1  # Adjustment to water stress thresholds depending on daily ET0 (0 = No, 1 = Yes)
        )
        self.Aer = (
            5  # Vol (%) below saturation at which stress begins to occur due to deficient aeration
        )
        self.LagAer = 3  # Number of days lag before aeration stress affects crop growth
        self.beta = 12  # Reduction (%) to p_lo3 when early canopy senescence is triggered
        self.a_Tr = 1  # Exponent parameter for adjustment of Kcx once senescence is triggered
        self.GermThr = 0.2  # Proportion of total water storage needed for crop to germinate
        self.CCmin = 0.05  # Minimum canopy size below which yield formation cannot occur
        self.MaxFlowPct = (
            100 / 3
        )  # Proportion of total flowering time (%) at which peak flowering occurs
        self.HIini = 0.01  # Initial harvest index
        self.bsted = 0.000138  # WP co2 adjustment parameter given by Steduto et al. 2007
        self.bface = 0.001165  # WP co2 adjustment parameter given by FACE experiments

        # added in Read_Model_Paramaters
        self.CropType = 3  # Crop Type (1 = Leafy vegetable, 2 = Root/tuber, 3 = Fruit/grain)
        self.PlantMethod = 1  # Planting method (0 = Transplanted, 1 =  Sown)
        self.CalendarType = 2  # Calendar Type (1 = Calendar days, 2 = Growing degree days)
        self.SwitchGDD = (
            0  # Convert calendar to GDD mode if inputs are given in calendar days (0 = No; 1 = Yes)
        )

        self.EmergenceCD = 0
        self.Canopy10PctCD = 0
        self.MaxRootingCD = 0
        self.SenescenceCD = 0
        self.MaturityCD = 0
        self.MaxCanopyCD = 0
        self.CanopyDevEndCD = 0
        self.HIstartCD = 0
        self.HIendCD = 0
        self.YldFormCD = 0

        self.Emergence = (
            80  # Growing degree/Calendar days from sowing to emergence/transplant recovery
        )
        self.MaxRooting = 1420  # Growing degree/Calendar days from sowing to maximum rooting
        self.Senescence = 1420  # Growing degree/Calendar days from sowing to senescence
        self.Maturity = 1670  # Growing degree/Calendar days from sowing to maturity
        self.HIstart = 850  # Growing degree/Calendar days from sowing to start of yield formation
        self.Flowering = 190  # Duration of flowering in growing degree/calendar days (-999 for non-fruit/grain crops)
        self.YldForm = 775  # Duration of yield formation in growing degree/calendar days
        self.HIend = 0
        self.MaxCanopy = 0
        self.CanopyDevEnd = 0
        self.Canopy10Pct = 0

        self.GDDmethod = 2  # Growing degree day calculation method
        self.Tbase = 8  # Base temperature (degC) below which growth does not progress
        self.Tupp = 30  # Upper temperature (degC) above which crop development no longer increases
        self.PolHeatStress = 1  # Pollination affected by heat stress (0 = No, 1 = Yes)
        self.Tmax_up = 40  # Maximum air temperature (degC) above which pollination begins to fail
        self.Tmax_lo = 45  # Maximum air temperature (degC) at which pollination completely fails
        self.PolColdStress = 1  # Pollination affected by cold stress (0 = No, 1 = Yes)
        self.Tmin_up = 10  # Minimum air temperature (degC) below which pollination begins to fail
        self.Tmin_lo = 5  # Minimum air temperature (degC) at which pollination completely fails
        self.TrColdStress = 1  # Transpiration affected by cold temperature stress (0 = No, 1 = Yes)
        self.GDD_up = 12  # Minimum growing degree days (degC/day) required for full crop transpiration potential
        self.GDD_lo = 0  # Growing degree days (degC/day) at which no crop transpiration occurs
        self.Zmin = 0.3  # Minimum effective rooting depth (m)
        self.Zmax = 1.7  # Maximum rooting depth (m)
        self.fshape_r = 1.3  # Shape factor describing root expansion
        self.SxTopQ = 0.0480  # Maximum root water extraction at top of the root zone (m3/m3/day)
        self.SxBotQ = (
            0.0117  # Maximum root water extraction at the bottom of the root zone (m3/m3/day)
        )

        self.SxTop = 0.0
        self.SxBot = 0.0

        self.SeedSize = (
            6.5  # Soil surface area (cm2) covered by an individual seedling at 90% emergence
        )
        self.PlantPop = 75_000  # Number of plants per hectare
        self.CCx = 0.96  # Maximum canopy cover (fraction of soil cover)
        self.CDC = 0.01  # Canopy decline coefficient (fraction per GDD/calendar day)
        self.CGC = 0.0125  # Canopy growth coefficient (fraction per GDD)
        self.CDC_CD = 0.01  # Canopy decline coefficient (fraction per GDD/calendar day)
        self.CGC_CD = 0.0125  # Canopy growth coefficient (fraction per GDD)
        self.Kcb = 1.05  # Crop coefficient when canopy growth is complete but prior to senescence
        self.fage = 0.3  #  Decline of crop coefficient due to ageing (%/day)
        self.WP = 33.7  # Water productivity normalized for ET0 and C02 (g/m2)
        self.WPy = 100  # Adjustment of water productivity in yield formation stage (% of WP)
        self.fsink = 0.5  # Crop performance under elevated atmospheric CO2 concentration (%/100)
        self.HI0 = 0.48  # Reference harvest index
        self.dHI_pre = (
            0  # Possible increase of harvest index due to water stress before flowering (%)
        )
        self.a_HI = 7  # Coefficient describing positive impact on harvest index of restricted vegetative growth during yield formation
        self.b_HI = 3  # Coefficient describing negative impact on harvest index of stomatal closure during yield formation
        self.dHI0 = 15  # Maximum allowable increase of harvest index above reference value
        self.Determinant = 1  # Crop Determinancy (0 = Indeterminant, 1 = Determinant)
        self.exc = 50  # Excess of potential fruits
        self.p_up = np.zeros(
            4
        )  # Upper soil water depletion threshold for water stress effects on affect canopy expansion
        self.p_lo = np.zeros(
            4
        )  # Lower soil water depletion threshold for water stress effects on canopy expansion
        self.fshape_w = np.ones(
            4
        )  # Shape factor describing water stress effects on canopy expansion

        self.CC0 = 0.0

        self.HIGC = 0.0
        self.tLinSwitch = 0
        self.dHILinear = 0.0

        self.fCO2 = 0.0

        self.FloweringCD = 0
        self.FloweringEnd = 0.0


CropStructNT = typing.NamedTuple("CropStructNT", crop_spec)
CropStructNT_type_sig= types.NamedTuple(tuple(dict(crop_spec).values()),CropStructNT)





# Cell
InitCond_spec = [
    ("AgeDays", float64),
    ("AgeDays_NS", float64),
    ("AerDays", float64),
    ("AerDaysComp", float64[:]),
    ("IrrCum", float64),
    ("DelayedGDDs", float64),
    ("DelayedCDs", float64),
    ("PctLagPhase", float64),
    ("tEarlySen", float64),
    ("GDDcum", float64),
    ("DaySubmerged", float64),
    ("IrrNetCum", float64),
    ("DAP", int64),
    ("Epot", float64),
    ("Tpot", float64),
    ("PreAdj", boolean),
    ("CropMature", boolean),
    ("CropDead", boolean),
    ("Germination", boolean),
    ("PrematSenes", boolean),
    ("HarvestFlag", boolean),
    ("GrowingSeason", boolean),
    ("YieldForm", boolean),
    ("Stage2", boolean),
    ("WTinSoil", boolean),
    ("Stage", float64),
    ("Fpre", float64),
    ("Fpost", float64),
    ("fpost_dwn", float64),
    ("fpost_upp", float64),
    ("HIcor_Asum", float64),
    ("HIcor_Bsum", float64),
    ("Fpol", float64),
    ("sCor1", float64),
    ("sCor2", float64),
    ("HIref", float64),
    ("GrowthStage", float64),
    ("TrRatio", float64),
    ("rCor", float64),
    ("CC", float64),
    ("CCadj", float64),
    ("CC_NS", float64),
    ("CCadj_NS", float64),
    ("B", float64),
    ("B_NS", float64),
    ("HI", float64),
    ("HIadj", float64),
    ("CCxAct", float64),
    ("CCxAct_NS", float64),
    ("CCxW", float64),
    ("CCxW_NS", float64),
    ("CCxEarlySen", float64),
    ("CCprev", float64),
    ("ProtectedSeed", int64),
    ("Y", float64),
    ("Zroot", float64),
    ("CC0adj", float64),
    ("SurfaceStorage", float64),
    ("zGW", float64),
    ("th_fc_Adj", float64[:]),
    ("th", float64[:]),
    ("thini", float64[:]),
    ("TimeStepCounter", int64),
    ("P", float64),
    ("Tmax", float64),
    ("Tmin", float64),
    ("Et0", float64),
    ("GDD", float64),
    ("Wsurf", float64),
    ("EvapZ", float64),
    ("Wstage2", float64),
    ("Depletion", float64),
    ("TAW", float64),
]


#@jitclass(spec)
class InitCondClass:
    """
    The InitCond Class contains all Paramaters and variables used in the simulation

    updated each timestep with the name NewCond


    """

    def __init__(self, num_comp):
        # counters
        self.AgeDays = 0
        self.AgeDays_NS = 0
        self.AerDays = 0
        self.AerDaysComp = np.zeros(num_comp)
        self.IrrCum = 0
        self.DelayedGDDs = 0
        self.DelayedCDs = 0
        self.PctLagPhase = 0
        self.tEarlySen = 0
        self.GDDcum = 0
        self.DaySubmerged = 0
        self.IrrNetCum = 0
        self.DAP = 0
        self.Epot = 0
        self.Tpot = 0

        # States
        self.PreAdj = False
        self.CropMature = False
        self.CropDead = False
        self.Germination = False
        self.PrematSenes = False
        self.HarvestFlag = False
        self.GrowingSeason = False
        self.YieldForm = False
        self.Stage2 = False

        self.WTinSoil = False

        # HI
        self.Stage = 1
        self.Fpre = 1
        self.Fpost = 1
        self.fpost_dwn = 1
        self.fpost_upp = 1

        self.HIcor_Asum = 0
        self.HIcor_Bsum = 0
        self.Fpol = 0
        self.sCor1 = 0
        self.sCor2 = 0
        self.HIref = 0.0

        # GS
        self.GrowthStage = 0

        # Transpiration
        self.TrRatio = 1

        # crop growth
        self.rCor = 1

        self.CC = 0
        self.CCadj = 0
        self.CC_NS = 0
        self.CCadj_NS = 0
        self.B = 0
        self.B_NS = 0
        self.HI = 0
        self.HIadj = 0
        self.CCxAct = 0
        self.CCxAct_NS = 0
        self.CCxW = 0
        self.CCxW_NS = 0
        self.CCxEarlySen = 0
        self.CCprev = 0
        self.ProtectedSeed = 0
        self.Y = 0

        self.Zroot = 0.
        self.CC0adj = 0
        self.SurfaceStorage = 0
        self.zGW = -999

        self.th_fc_Adj = np.zeros(num_comp)
        self.th = np.zeros(num_comp)
        self.thini = np.zeros(num_comp)

        self.TimeStepCounter = 0

        self.P = 0
        self.Tmax = 0
        self.Tmin = 0
        self.Et0 = 0
        self.GDD = 0

        self.Wsurf = 0
        self.EvapZ = 0
        self.Wstage2 = 0

        self.Depletion = 0
        self.TAW = 0














# Cell
spec = [
    ("Act", float64),
    ("Sat", float64),
    ("Fc", float64),
    ("Wp", float64),
    ("Dry", float64),
]


#@jitclass(spec)
class WevapClass(object):
    """
    stores soil water contents in the evaporation layer

    **Attributes:**\n


    `Sat` : `float` :  Water storage in evaporation layer at saturation (mm)

    `Fc` : `float` :  Water storage in evaporation layer at Field Capacity (mm)

    `Wp` : `float`:  Water storage in evaporation layer at Wilting Point (mm)

    `Dry` : `float` : Water storage in evaporation layer at air dry (mm)

    `Act` : `float` : Actual Water storage in evaporation layer (mm)

    """

    def __init__(self):
        self.Sat = 0.0
        self.Fc = 0.0
        self.Wp = 0.0
        self.Dry = 0.0
        self.Act = 0.0


# Cell
SoilProfileNT_spec = [
    ("Comp", int64[:]),
    ("dz", float64[:]),
    ("Layer", int64[:]),
    ("dzsum", float64[:]),
    ("th_fc", float64[:]),
    ("th_s", float64[:]),
    ("th_wp", float64[:]),
    ("Ksat", float64[:]),
    ("Penetrability", float64[:]),
    ("th_dry", float64[:]),
    ("tau", float64[:]),
    ("zBot", float64[:]),
    ("zTop", float64[:]),
    ("zMid", float64[:]),
    ("th_fc_Adj", float64[:]),
    ("aCR", float64[:]),
    ("bCR", float64[:]),
]


#@jitclass(spec)
class SoilProfileClass:
    """

    **Attributes:**\n

    `Comp` : `list` :

    `Layer` : `list` :

    `dz` : `list` :

    `dzsum` : `list` :

    `zBot` : `list` :

    `zTop` : `list` :

    `zMid` : `list` :

    """

    def __init__(self, length):

        self.Comp = np.zeros(length, dtype=np.int64)
        self.dz = np.zeros(length, dtype=np.float64)
        self.Layer = np.zeros(length, dtype=np.int64)
        self.dzsum = np.zeros(length, dtype=np.float64)
        self.th_fc = np.zeros(length, dtype=np.float64)
        self.th_s = np.zeros(length, dtype=np.float64)
        self.th_wp = np.zeros(length, dtype=np.float64)
        self.Ksat = np.zeros(length, dtype=np.float64)
        self.Penetrability = np.zeros(length, dtype=np.float64)
        self.th_dry = np.zeros(length, dtype=np.float64)
        self.tau = np.zeros(length, dtype=np.float64)
        self.zBot = np.zeros(length, dtype=np.float64)
        self.zTop = np.zeros(length, dtype=np.float64)
        self.zMid = np.zeros(length, dtype=np.float64)
        self.th_fc_Adj = np.zeros(length, dtype=np.float64)
        self.aCR = np.zeros(length, dtype=np.float64)
        self.bCR = np.zeros(length, dtype=np.float64)


SoilProfileNT = typing.NamedTuple("SoilProfileNT", SoilProfileNT_spec)
SoilProfileNT_typ_sig= types.NamedTuple(tuple(dict(SoilProfileNT_spec).values()),SoilProfileNT)


# Cell
spec = [
    ("Rz", float64),
    ("Zt", float64),
]


#@jitclass(spec)
class TAWClass:
    """
    **Attributes:**\n



    `Rz` : `float` : .

    `Zt` : `float` : .




    """

    def __init__(self):
        self.Rz = 0.0
        self.Zt = 0.0


# Cell
spec = [
    ("Rz", float64),
    ("Zt", float64),
]


#@jitclass(spec)
class DrClass:

    """

    **Attributes:**\n

    `Rz` : `float` : .

    `Zt` : `float` : .


    """

    def __init__(self):
        self.Rz = 0.0
        self.Zt = 0.0


# Cell
thRZ_spec = [
    ("Act", float64),
    ("S", float64),
    ("FC", float64),
    ("WP", float64),
    ("Dry", float64),
    ("Aer", float64),
]


#@jitclass(spec)
class thRZClass(object):
    """
    root zone water content

    **Attributes:**\n



    `Act` : `float` : .

    `S` : `float` : .

    `FC` : `float` : .

    `WP` : `float` : .

    `Dry` : `float` : .

    `Aer` : `float` : .



    """

    def __init__(self):
        self.Act = 0.0
        self.S = 0.0
        self.FC = 0.0
        self.WP = 0.0
        self.Dry = 0.0
        self.Aer = 0.0


thRZNT = typing.NamedTuple("thRZNT", thRZ_spec)
thRZNT_type_sig= types.NamedTuple(tuple(dict(thRZ_spec).values()),thRZNT)


# Cell
Ksw_spec = [
    ("Exp", float64),
    ("Sto", float64),
    ("Sen", float64),
    ("Pol", float64),
    ("StoLin", float64),
]


#@jitclass(spec)
class KswClass(object):

    """
    water stress coefficients

    **Attributes:**\n


    `Exp` : `float` : .

    `Sto` : `float` : .

    `Sen` : `float` : .

    `Pol` : `float` : .

    `StoLin` : `float` : .



    """

    def __init__(self):
        self.Exp = 1.0
        self.Sto = 1.0
        self.Sen = 1.0
        self.Pol = 1.0
        self.StoLin = 1.0




KswNT = typing.NamedTuple("KswNT", Ksw_spec)
KswNT_type_sig= types.NamedTuple(tuple(dict(Ksw_spec).values()),KswNT)






# Cell
Kst_spec = [
    ("PolH", float64),
    ("PolC", float64),
]


#@jitclass(spec)
class KstClass(object):

    """
    temperature stress coefficients

    **Attributes:**\n


    `PolH` : `float` : heat stress

    `PolC` : `float` : cold stress


    """

    def __init__(self):
        self.PolH = 1.0
        self.PolC = 1.0


KstNT = typing.NamedTuple("KstNT", Kst_spec)
KstNT_type_sig= types.NamedTuple(tuple(dict(Kst_spec).values()),KstNT)





# Cell
spec = [
    ("RefConc", float64),
    ("CurrentConc", float64),
]


#@jitclass(spec)
class CO2Class(object):

    """

    **Attributes:**\n


    `RefConc` : `float` : reference CO2 concentration

    `CurrentConc` : `float` : current CO2 concentration

    """

    def __init__(self):
        self.RefConc = 369.41
        self.CurrentConc = 0.0

