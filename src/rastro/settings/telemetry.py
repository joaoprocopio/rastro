from rastro_shared_kernel.env import get_env

SERVICE_NAMESPACE = get_env(
    "RASTRO_SERVICE_NAMESPACE",
    default="rastro",
)

SERVICE_NAME = get_env(
    "RASTRO_SERVICE_NAME",
    default="rastro",
)

DEPLOYMENT_ID = get_env(
    "RASTRO_DEPLOYMENT_ID",
    default="2f92ca37",
)

DEPLOYMENT_ENVIRONMENT = get_env(
    "RASTRO_DEPLOYMENT_ENVIRONMENT",
    default="dev",
)

OTEL_GRPC_ENDPOINT = get_env(
    "RASTRO_OTEL_GRPC_ENDPOINT",
    default="localhost:4317",
)
