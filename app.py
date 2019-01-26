# dependencies

# Flask( Server)
from flask import Flask, jsonify, render_template, request, flash, redirect

# SQL ALchemy (ORM)
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine,func,desc,select
import pandas as pd
import numpy as np

# database setup

engine = create_engine("sqlite:///DataSets/belly_button_biodiversity.sqlite")

# reflect an exisiting database into a new model
Base = automap_base()

#reflect tables
Base.prepare(engine, reflect=True)

#save referances to the table
OTU = Base.classes.otu
Samples = Base.classes.samples
Samples_Metadata = Base.classes.samples_metadata

# Create session(link from Python to # DB)
session = Session(engine)

# Flask setup
app = Flask(__name__)

# Flask Routes

# Returns the dashboard homepage
@app.route("/")
def index():
    return render_template("index.html")

# Returns a list of sample names
@app.route('/names')
def names():
    # Return list of sample names

    #Use Pandas to perform the sql query

    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt,session.bind)
    df.set_index('otu_id',inplace=True)

    # Return a list of the colum names(samle names)
    return jsonify(list(df.columns))

# Returns a list of OTU description
@app.route("/otu")
def otu():
    results = session.query(OTU.lowest_taxonomic_unit_found).all()

    # Use numpy ravel to extract list o ftuples into lis of OTU descriptions
    otu_list = list(np.ravel(results))
    return jsonify(otu_list)

# Returns a json dictionary of sample Samples_Metadata
#MetaData for a given sample.
@app.route("/metadata/<sample>")
def sample_metadata(sample):
    sel = [Samples_Metadata.SAMPLEID, Samples_Metadata.ETHNICITY,
           Samples_Metadata.GENDER, Samples_Metadata.AGE,
           Samples_Metadata.LOCATION, Samples_Metadata.BBTYPE]

    results = session.query(*sel).\
    filter(Samples_Metadata.SAMPLEID == sample[3:]).all()

    # Create a dictionary entry for each row of metadata information
    sample_metadata = {}
    for result in results:
        sample_metadata['SAMPLEID'] = result[0]
        sample_metadata['ETHNICITY'] = result[1]
        sample_metadata['GENDER'] = result[2]
        sample_metadata['AGE'] = result[3]
        sample_metadata['LOCATION'] = result[4]
        sample_metadata['BBTYPE'] = result[5]

    return jsonify(sample_metadata)


# Return a list of dictionaries containing sorted lists  for `otu_ids`and `sample_values`
@app.route('/samples/<sample>')
def samples(sample):
    """Return a list dictionaries containing `otu_ids` and `sample_values`."""
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)

    # Make sure that the sample was found in the columns, else throw an error
    if sample not in df.columns:
        return jsonify(f"Error! Sample: {sample} Not Found!"), 400

    # Return any sample values greater than 1
    df = df[df[sample] > 1]

    # Sort the results by sample in descending order
    df = df.sort_values(by=sample, ascending=0)

    # Format the data to send as json
    data = [{
        "otu_ids": df[sample].index.values.tolist(),
        "sample_values": df[sample].values.tolist()
    }]
    return jsonify(data)
if __name__ == "__main__":
    app.run(debug=True)
