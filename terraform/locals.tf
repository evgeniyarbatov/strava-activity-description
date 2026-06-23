locals {
  openweather_api_key = trimspace(split("=", file("${path.module}/../openweather.env"))[1])
  tomtom_api_key      = trimspace(split("=", file("${path.module}/../tomtom.env"))[1])
}
