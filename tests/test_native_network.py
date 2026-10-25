"""Antigravity may use identity/model APIs, not Google data APIs or host services."""

import json

from test_native_policy import SCRIPT, node_json


def function(name):
    source = SCRIPT.read_text()
    marker = f"function {name}("
    return marker + source.split(marker, 1)[1].split("\n}\n", 1)[0] + "\n}\n"


def test_antigravity_api_exceptions_are_exact_and_vendor_scoped():
    requests = [
        {"host": host, "port": port}
        for host, port in [
            ("oauth2.googleapis.com", 443),
            ("daily-cloudcode-pa.googleapis.com", 443),
            ("www.googleapis.com", 443),
            ("drive.googleapis.com", 443),
            ("gmail.googleapis.com", 443),
            ("evil.oauth2.googleapis.com", 443),
            ("oauth2.googleapis.com", 80),
            ("localhost", 443),
            ("127.0.0.1", 443),
            ("[::1]", 443),
            ("example.local", 443),
            ("example.com", 443),
        ]
    ]
    probe = (
        'import {isIP} from "node:net";\n'
        + function("publicDestination")
        + f"const requests = {json.dumps(requests)};\n"
        + 'let plan = {vendor:"antigravity"};\n'
        + "const antigravity = requests.map(publicDestination);\n"
        + 'plan = {vendor:"pi"};\n'
        + "console.log(JSON.stringify({antigravity, pi:requests.map(publicDestination)}));"
    )
    result = node_json(probe)
    assert result["antigravity"] == [
        True,
        True,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
    ]
    assert result["pi"] == [False] * 11 + [True]


def test_google_identity_path_filter_does_not_admit_drive_or_opaque_requests():
    paths = [
        "https://www.googleapis.com/oauth2/v2/userinfo",
        "https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=synthetic",
        "https://www.googleapis.com/drive/v3/files",
        "http://www.googleapis.com/oauth2/v2/userinfo",
        "https://www.googleapis.com/oauth2/v2/userinfo/extra",
    ]
    probe = (
        function("identityRequest")
        + f"const paths = {json.dumps(paths)};\n"
        + "console.log(JSON.stringify(paths.map(url => identityRequest(new Request(url)).action)));"
    )
    assert node_json(probe) == ["allow", "allow", "deny", "deny", "deny"]
