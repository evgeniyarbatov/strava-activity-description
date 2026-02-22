# Strava Activity Description

Generate short Strava activity descriptions from run polylines, weather, traffic, and prior history.

#### Artistic

> In Hà Nội's gentle morning drizzle, legs slice through dew-kissed streets, breeze whispering past ears as clouds shift overhead.

#### Monk

> As I begin my run under the gentle caress of the dew-kissed morning, the light rain whispers softly against my skin, reminding me of the transient nature of all things.

#### Memory

> The rain had softened to a drizzle, barely kissing my cheeks as I ran. A lone bicycle bell chimed behind me, its sound swallowed by the dampened morning.

#### Scientist

> Initiating run at 07:04 in Hà Nội, Vietnam; conditions: light rain, overcast clouds. Duration expeditious, no significant conversation exchanged throughout the compact route.

## Run

1. Add GPX/TCX to `data/raw`.
2. Run `make analyze` to merge GPX/TCX and enrich activities with weather/traffic context.
3. Run `make describe` to generate descriptions in `data/descriptions`.

## Dev Setup

1. Create the venv and install dependencies: `make install`.
2. Add API keys in `api-keys/`: `openweather.env`, `tomtom.env`, and `gemini.env`.
3. Configure Terraform + AWS: set AWS credentials in your shell for the target account; update the S3 backend in `terraform/terraform.tf`; set latitude/longitude for weather + traffic sampling
4. Deploy infrastructure: `cd terraform && terraform init`, then `terraform apply`
