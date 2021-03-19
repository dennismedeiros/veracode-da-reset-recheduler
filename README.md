# Veracode Dynamic Analysis Reset Recheduler
This program is designed to reset all recurrent scheduled analysis jobs configure for one year that it finds that have expired.


## Setup
### Clone repository
```
git clone https://github.com/dennismedeiros/veracode-da-reset-recheduler.git
```

### Install dependencies
For the application to run it is required the following dependiencies be installed
* Python >= 3.0  
* requests >= 2.21.0
* veracode-api-signing >= 19.9.0

To retive dependencies from the command line:

```
cd veracode-da-reset-rescheduler
pip install -r requirements.txt
```

## Run program
To run the program you are **required** to have your veracode credentials installed locally to your user directory. Please reference [here](https://help.veracode.com/r/c_configure_api_cred_file) for information regarding configuring and set up of your credentials within the Vercode Help Center. 

The account roles needed for this program to work are as follows:
* Administrator

### Credential file
Save Veracode API credentials in `~/.veracode/credentials`
```
    [default]
    veracode_api_key_id = <YOUR_API_KEY_ID>
    veracode_api_key_secret = <YOUR_API_KEY_SECRET>
```
#### To perform a *dry* run of the program to review changes but not commit
```
C:> python veracode-da-reset-scheduler -d
```
#### To perform a **live** run of the program to peform changes and commit
```
C:> python veracode-da-reset-scheduler -x
```