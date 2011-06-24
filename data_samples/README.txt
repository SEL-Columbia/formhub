This samples directory is for data that can be substituted in during the load_fixtures step.

It will be:

  1. anonymous (all local data and coordinates will be faked.)
  2. smaller (able to be loaded into the database quickly.)
  3. substitutable (able to populate elements of the UI in a manner similar to the real, cleaned data files.)

It will meet these criteria so that we can commit it to the repository and have code & data that will work when it's cloned.