from app.models import PidAssignment, RegisterResponse


PID_ASSIGNMENTS: dict[str, list[str]] = {
    "raspi-01": [
        "pid_3f9a0c8e12d44bb7a98f21cd",
        "pid_81c2fb771a0945c4b62e03aa",
        "pid_f4d812bafe98490ab2731e28",
        "pid_20b17e5f10fd4cd4a9cb743e",
        "pid_a9374b8267d140a1802a935c",
    ],
    "raspi-02": [
        "pid_b2d80ad7910c4a45bbd5688e",
        "pid_10cb620831834cc8a177d1dd",
        "pid_de0a8e6a4a974c9eb2bd39af",
        "pid_b8a52e3a8c774a14a61d8b12",
        "pid_37ef4af5c8084c278df6548a",
    ],
    "raspi-03": [
        "pid_84c353dbcb9c414aa173f878",
        "pid_cb01d475327045649cc32763",
        "pid_8a906fa24e434055bb8d3567",
        "pid_2b95f08d650145379bc69df1",
        "pid_b94483d2ff234a86a1b09d37",
    ],
    "phone-01": [
        "pid_64b79ea172304899be1170aa",
        "pid_1fb8f25e8c4d4f91bbd30e72",
        "pid_773a12f01f224ca78db11939",
        "pid_f8b412c67e194ebba0e9c4dd",
        "pid_aa0391787f5c42f59478be02",
    ],
    "phone-02": [
        "pid_97df0e6b8b2d4ed58a19dcb4",
        "pid_c42a7b68d5574dddbebc6d79",
        "pid_1d9f2a047b3348658a77b2ce",
        "pid_ea3f79c0b6fb407da297a4a8",
        "pid_5c87cb0df47340a891cb9e4b",
    ],
}

REGISTERED_NODES: dict[str, dict[str, str]] = {
    "raspi@example.com": {
        "node_id": "raspi-01",
        "device_type": "raspi",
    },
    "raspi2@example.com": {
        "node_id": "raspi-02",
        "device_type": "raspi",
    },
    "raspi3@example.com": {
        "node_id": "raspi-03",
        "device_type": "raspi",
    },
    "phone1@example.com": {
        "node_id": "phone-01",
        "device_type": "phone",
    },
    "phone2@example.com": {
        "node_id": "phone-02",
        "device_type": "phone",
    },
}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def list_assignments() -> list[PidAssignment]:
    return [
        PidAssignment(node_id=node_id, pids=pids)
        for node_id, pids in sorted(PID_ASSIGNMENTS.items())
    ]


def get_pids_for_node(node_id: str) -> list[str] | None:
    return PID_ASSIGNMENTS.get(node_id)


def register_node(email: str) -> RegisterResponse | None:
    normalized_email = normalize_email(email)
    registration = REGISTERED_NODES.get(normalized_email)
    if registration is None:
        return None

    node_id = registration["node_id"]
    return RegisterResponse(
        email=normalized_email,
        node_id=node_id,
        device_type=registration["device_type"],  # type: ignore[arg-type]
        pids=PID_ASSIGNMENTS[node_id],
    )


def is_valid_pid(node_id: str, pid: str) -> bool:
    return pid in PID_ASSIGNMENTS.get(node_id, [])
