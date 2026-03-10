export const name = "ping";

export const description = "A simple ping tool to check server liveness";

export const inputSchema = {
    type: "object",
    properties: {}
};

export const handler = async (args: any) => {
    return {
        content: [{ type: "text", text: "pong" }]
    };
};
