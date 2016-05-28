import datetime as dt

from sklearn.tree import DecisionTreeRegressor
import numpy as np

from app import app
from app import models
from app.database import session
from mongo.timeseries import query
from training import munging
from training import util


forward = 7


def training_days(current):
    ''' Set a new number of training days to search through. '''
    delta = 7
    lower = max(current - delta, 1)
    upper = current + delta
    days = list(range(lower, upper + 1))
    return days


def optimize(regressor, training):
    ''' Search for the optimal number of training days. '''
    # Number of days on which the regressor is trained
    backwards = training_days(training.backward)
    # Current time
    now = dt.datetime.now()
    # A week ago
    then = now - dt.timedelta(days=forward)
    # Longest time ago
    since = then - dt.timedelta(days=max(backwards))
    # Get all the necessary data
    try:
        data = query.station(training.station.city.name,
                             training.station.name,
                             since=since,
                             until=now)
    except:
        app.logger.info("No data found for '{0}' from {1} till {2}".format(
            training.station.name,
            since.date(),
            now.date()
        ))
        return False
    # Run a grid search to obtain a regressor
    df = munging.prepare(data)
    best = {
        'moment': now,
        'backward': None,
        'score': np.inf
    }
    # Go through all the possible backward/forward combinations
    for backward in backwards:
        # Define the training timeline
        timeline = [then - dt.timedelta(days=backward), then, now]
        # Define the train and test sets
        train = df.truncate(before=timeline[0], after=timeline[1])
        test = df.truncate(before=timeline[1], after=timeline[2])
        if len(train) == 0 or len(test) == 0:
            app.logger.warning("Not enough data for training '{0}' with timeline {1}".format(
                training.station.name,
                [time.date().isoformat() for time in timeline]
            ))
            continue
        # Split the training set into features and targets
        X_train, Y_train = munging.split(dataframe=train, target='bikes')
        # Train the regressor
        regressor.fit(X_train, Y_train)
        # Split the test set into features and targets
        X_test, Y_test = munging.split(dataframe=test, target='bikes')
        # Predict the outcome the test set
        prediction = regressor.predict(X_test)
        # Compute the mean absolute error
        score = np.mean(abs(Y_test - prediction))
        # Compare the obtained score to the current best score
        if score < best['score']:
            best['backward'] = backward
            best['score'] = score
    # Select data backwards according to the grid search
    data = df.truncate(before=now - dt.timedelta(days=best['backward']), after=now)
    try:
        X, Y = munging.split(dataframe=data, target='bikes')
        regressor.fit(X, Y)
        best['regressor'] = regressor
        return best
    except ValueError:
        return False


def update(station):
    ''' Train a regressor for a station and save it. '''
    method = DecisionTreeRegressor(max_depth=6)
    # Train a regressor for the bikes and another one the spaces
    best = optimize(method, station.training)
    if best == False:
        return
    # Update the database
    station.training.moment = best['moment']
    station.training.backward = best['backward']
    station.training.forward = forward
    station.training.error = best['score']
    session.commit()
    # Save the regressor
    util.save_regressor(best['regressor'],
                        station.city.name,
                        station.name)

for station in models.Station.query:
    update(station)
