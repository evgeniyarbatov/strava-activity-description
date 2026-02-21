locals {
  openweather_api_key = coalesce(
    var.openweather_api_key,
    trimspace(element(split("=", file("/Users/zhenya/gitRepo/api-secrets/openweather.env")), length(split("=", file("/Users/zhenya/gitRepo/api-secrets/openweather.env"))) - 1))
  )
  tomtom_api_key = coalesce(
    var.tomtom_api_key,
    trimspace(element(split("=", file("/Users/zhenya/gitRepo/api-secrets/tomtom.env")), length(split("=", file("/Users/zhenya/gitRepo/api-secrets/tomtom.env"))) - 1))
  )
}
