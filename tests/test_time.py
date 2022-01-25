def test_compile_time():
    import time

    start = time.time()
    import aquacrop  # tests jit compile time

    end = time.time()
    t = end - start
    print(f"compile time: {round(t,3)}")
    assert t < 60


def test_tunis_model_run(n=1):


    from aquacrop.classes import SoilClass, CropClass, InitWCClass
    from aquacrop.core import prepare_weather, get_filepath, AquaCropModel
    import time

    # locate built in weather file
    filepath = get_filepath("tunis_climate.txt")
    weather_data = prepare_weather(filepath)

    start = time.time()

    for sim_i in range(n):
        # start of jitted code
        sandy_loam = SoilClass(soilType="SandyLoam")
        wheat = CropClass("Wheat", PlantingDate="10/01")
        InitWC = InitWCClass(value=["FC"])
        # combine into aquacrop model and specify start and end simulation date
        model = AquaCropModel(
            SimStartTime=f"{1979}/10/01",
            SimEndTime=f"{1985}/05/30",
            wdf=weather_data,
            Soil=sandy_loam,
            Crop=wheat,
            InitWC=InitWC,
        )
        # initilize model
        model.initialize()
        # run model till termination
        model.step(till_termination=True)

    end = time.time()
    t = end - start
    print(f"total sim time for {n} repetitions: {round(t,3)}")
    assert t < 60

test_compile_time()
test_tunis_model_run()
test_tunis_model_run(10)