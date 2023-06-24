import io.pedestal.http as http
import io.pedestal.http.route as route
import clojure.spec.gen.alpha as gen
import clojure.tools.logging as log
import environ.core as env
import mount.core as mount
import decimals.interceptors as i
import decimals.analytics as a
import decimals.specs

service_map = {
    http.routes: i.routes,
    http.allowed_origins: {
        http.allowed_origins: gen.read_string(origins) if origins := env.get('allowed-origins') else None,
        http.methods: "GET,POST"
    },
    http.type: http.jetty,
    http.host: "0.0.0.0",
    http.port: 8910
}


def start():
    mount.start()
    http.start(http.create_server(service_map))


def main(*args):
    print("\nCreating your server...")
    start()


# For interactive development
server = None


def start_dev():
    mount.start()
    global server
    server = http.start(http.create_server(dict(service_map, **{http.join: False})))


def stop_dev():
    http.stop(server)


def restart():
    stop_dev()
    start_dev()


# restart()
