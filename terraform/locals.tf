locals {
  openweather_api_key = trimspace(split("=", file("${path.root}/../api-keys/openweather.env"))[1])
  tomtom_api_key      = trimspace(split("=", file("${path.root}/../api-keys/tomtom.env"))[1])
}
