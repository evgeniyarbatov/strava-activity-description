locals {
  openweather_api_key = coalesce(
    var.openweather_api_key,
    trimspace(element(split("=", file("/Users/zhenya/gitRepo/[private]/openweather.env")), length(split("=", file("/Users/zhenya/gitRepo/[private]/openweather.env"))) - 1))
  )
  tomtom_api_key = coalesce(
    var.tomtom_api_key,
    trimspace(element(split("=", file("/Users/zhenya/gitRepo/[private]/tomtom.env")), length(split("=", file("/Users/zhenya/gitRepo/[private]/tomtom.env"))) - 1))
  )
}
