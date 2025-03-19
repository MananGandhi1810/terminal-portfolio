import asyncio
import socket
from data import projects, languages, librariesAndFrameworks, tools

PORT = 6379
HOST = "127.0.0.1"

clients = set()


def parse_resp(data):
    if not data:
        return None

    data_str = data.decode("utf-8", errors="ignore")

    first_byte = data_str[0]

    if first_byte == "+":
        return data_str[1:].strip()

    elif first_byte == "-":
        return f"Error: {data_str[1:].strip()}"

    elif first_byte == ":":
        return int(data_str[1:].trip())

    elif first_byte == "$":
        parts = data_str.split("\r\n", 2)
        if len(parts) >= 3:
            length = int(parts[0][1:])
            if length == -1:
                return None
            return parts[1]
        return None

    elif first_byte == "*":
        result = []
        lines = data_str.split("\r\n")

        if len(lines) < 2:
            return None

        count = int(lines[0][1:])
        if count == -1:
            return None

        line_index = 1
        for _ in range(count):
            if line_index >= len(lines):
                break

            if lines[line_index].startswith("$"):
                length = int(lines[line_index][1:])
                if length == -1:
                    result.append(None)
                else:
                    result.append(lines[line_index + 1])
                line_index += 2
        return result

    else:
        return data_str.strip()


async def handle_client(client, addr):
    clients.add(client)
    try:
        while True:
            data = await asyncio.get_event_loop().sock_recv(client, 1024)
            if not data:
                break

            parsed_data = parse_resp(data)

            print(f"Received raw: {data}")
            print(f"Parsed: {parsed_data}")

            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                command = " ".join(str(item) for item in parsed_data)
                print(f"Command: {command}")

            response, success = handle_command(parsed_data)
            await send_message(client, response, success)
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        clients.remove(client)
        client.close()


async def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.setblocking(False)

    server.bind((HOST, PORT))
    server.listen()

    print(f"[*] Listening on {HOST}:{PORT}")

    loop = asyncio.get_event_loop()

    while True:
        client, addr = await loop.sock_accept(server)
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

        loop.create_task(handle_client(client, addr))


async def send_message(client, message, success=True):
    resp_encoded_message = f"{'+' if success else '-'}{message}\r\n".encode("utf-8")
    await asyncio.get_event_loop().sock_sendall(client, resp_encoded_message)


def handle_command(data):
    if not data or len(data) == 0:
        return "No Command", False
    command = data[0]
    args = data[1:] if len(data) > 1 else []
    response = ""
    success = True

    match command.upper():
        case "ABOUT":
            response = """
███╗   ███╗ █████╗ ███╗   ██╗ █████╗ ███╗   ██╗ ██████╗  █████╗ ███╗   ██╗██████╗ ██╗  ██╗██╗
████╗ ████║██╔══██╗████╗  ██║██╔══██╗████╗  ██║██╔════╝ ██╔══██╗████╗  ██║██╔══██╗██║  ██║██║
██╔████╔██║███████║██╔██╗ ██║███████║██╔██╗ ██║██║  ███╗███████║██╔██╗ ██║██║  ██║███████║██║
██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║╚██╗██║██║   ██║██╔══██║██║╚██╗██║██║  ██║██╔══██║██║
██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╔╝██║  ██║██║ ╚████║██████╔╝██║  ██║██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═╝                                                                                                        
I am Manan Gandhi, an 18 y/o engineering student, who loves to code and build software tools."""
        case "PROJECTS":
            if args:
                try:
                    project_index = int(args[0]) - 1
                    if 0 <= project_index < len(projects):
                        found_project = projects[project_index]
                        response = f"""
{found_project["projectName"]}
Description: {found_project["projectDescription"]}
Tech Stack: {', '.join(found_project["projectTechnologies"])}
URL: {found_project["projectLink"]}
"""
                    else:
                        response = "Project not found."
                except ValueError:
                    response = "Invalid project index."
            else:
                response = "These are the projects developed by me:\n"
                for index, project in enumerate(projects):
                    response += f"({index+1}) {project['projectName']} - {project['projectLink']}\n"
                response += (
                    "Use PROJECTS <number> to get more details about each project.\n"
                )
        case "SKILLS":
            response = "Languages:\n"
            for skill in languages:
                response += f"• {skill}\n"
            response += "\nLibraries & Frameworks:\n"
            for skill in librariesAndFrameworks:
                response += f"• {skill}\n"
            response += "\nTools:\n"
            for skill in tools:
                response += f"• {skill}\n"

    return response.strip(), success


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n[*] Server shutting down")
