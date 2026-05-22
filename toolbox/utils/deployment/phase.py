import copy


def inject_phase_middleware(compose: dict, phase_name: str) -> dict:
    """
    Patch a docker-compose dict to add a Traefik ForwardAuth phase-gate middleware
    on every HTTP router that has traefik.enable=true.
    """
    compose = copy.deepcopy(compose)

    for service_config in compose.get("services", {}).values():
        if not isinstance(service_config, dict):
            continue

        labels = service_config.get("labels", [])
        if not labels:
            continue

        # Normalise label list to dict
        if isinstance(labels, list):
            labels_dict: dict[str, str] = {}
            for label in labels:
                k, _, v = label.partition("=")
                labels_dict[k.strip()] = v.strip()
        else:
            labels_dict = dict(labels)

        if labels_dict.get("traefik.enable", "").lower() != "true":
            continue

        # Collect router names from traefik.http.routers.<name>.<field> labels
        router_names: set[str] = set()
        for key in labels_dict:
            parts = key.split(".")
            if len(parts) >= 5 and parts[:3] == ["traefik", "http", "routers"]:
                router_names.add(parts[3])

        for router_name in router_names:
            mw_name = f"phase-gate-{router_name}"
            phase_gate_url = f"http://phase-gate:8080/check?phase={phase_name}"

            labels_dict[f"traefik.http.middlewares.{mw_name}.forwardauth.address"] = phase_gate_url

            existing_key = f"traefik.http.routers.{router_name}.middlewares"
            existing = labels_dict.get(existing_key, "")
            labels_dict[existing_key] = f"{mw_name},{existing}" if existing else mw_name

        service_config["labels"] = [f"{k}={v}" for k, v in labels_dict.items()]

    return compose
