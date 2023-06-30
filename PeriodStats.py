from saleae.range_measurements import DigitalMeasurer
from math import sqrt

# 'User' parameters

# Set kWantRisingEdge False for falling edge driven measurements or True for
# rising edge driven measurements
kWantRisingEdge = True

class RunningSD:
    def __init__(self):
        self.n = 0
        self.oldMean = 0
        self.oldSum = 0

    def add(self, value):
        self.n += 1

        if self.n < 2:
            self.oldMean = value
            self.newMean = value
            self.oldSum = 0.0
            return

        self.newMean = self.oldMean + (value - self.oldMean) / float(self.n)
        self.newSum = self.oldSum + (value - self.oldMean) * (value - self.newMean)
        self.oldMean = self.newMean
        self.oldSum = self.newSum

    def StdDev(self):
        if self.n > 1:
            return sqrt(self.newSum / float(self.n - 1))

        return 0.0

class PeriodStatsMeasurer(DigitalMeasurer):
    supported_measurements = ['pMin', 'pMax', 'pSDev']

    '''
    Initialize PeriodStatsMeasurer object instance. An instance is created for
    each measurement session so this code is called once at the start of each
    measurement.

    process_data(...) is then called multiple times to process data in time
    order.

    After all data has been processed measure(...) is called to complete
    analysis and return a dictionary of results.
    '''
    def __init__(self, requested_measurements):
        super().__init__(requested_measurements)
        self.pMin = None
        self.pMean = 0.0
        self.pMax = None
        self.periodCount = 0.0
        self.lastTime = None
        self.lastState = None
        self.SDev = RunningSD()

    '''
    process_data() will be called one or more times per measurement with batches
    of data.

    data has the following interface:

      * Iterate over data to get transitions in the form of pairs of
        `Time`, Bitstate (`True` for high, `False` for low)

      * The first datum is at the first transition

    `Time` currently only allows taking a difference with another `Time`, to
    produce a `float` number of seconds
    '''
    def process_data(self, data):
        for t, bitstate in data:
            if bitstate != kWantRisingEdge:
                continue

            if self.lastState is None:
                self.lastState = bitstate
                self.lastTime = t

                # Can't generate stats for the first edge
                continue

            timeDelta = float(t - self.lastTime)
            self.lastTime = t

            # Interesting edge - rising edge if bitstate is true
            self.periodCount += 1
            self.pMean += timeDelta
            self.SDev.add(timeDelta)

            if self.pMin == None or timeDelta < self.pMin:
                self.pMin = timeDelta

            if self.pMax == None or timeDelta > self.pMax:
                self.pMax = timeDelta

    '''
    measure(...) is called after all the relevant data has been processed by
    process_data(...). It returns a dictionary of measurement results.
    '''
    def measure(self):
        values = {}

        if self.pMin != None:
            values['pMin'] = self.pMin
            values['pMean'] = self.pMean / self.periodCount
            values['pMax'] = self.pMax
            values['pSDev'] = self.SDev.StdDev()
            values['pCount'] = self.periodCount

            if self.pMean != None and self.pMean > 0.0:
                values['pFreq'] = self.periodCount / self.pMean

        return values
