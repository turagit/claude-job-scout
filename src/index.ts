import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

/**
 * Claude Job Scout MCP Server
 * Helps with CV management and LinkedIn job searches.
 */

const server = new Server(
    {
        name: "claude-job-scout",
        version: "1.0.0",
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

/**
 * TOOL DEFINITIONS
 */
const TOOLS = [
    {
        name: "analyze_cv",
        description: "Analyzes a CV/Resume (provided as text) and returns key skills, experience, and optimization tips.",
        inputSchema: {
            type: "object",
            properties: {
                cvText: { type: "string", description: "The full text content of the CV" },
            },
            required: ["cvText"],
        },
    },
    {
        name: "search_linkedin_jobs",
        description: "Searches for jobs on LinkedIn based on keywords and location.",
        inputSchema: {
            type: "object",
            properties: {
                keywords: { type: "string", description: "Job titles or skills (e.g., 'Software Engineer')" },
                location: { type: "string", description: "City, State or Remote" },
                limit: { type: "number", description: "Maximum number of results to return", default: 5 },
            },
            required: ["keywords"],
        },
    },
    {
        name: "optimize_cv_for_job",
        description: "Takes a CV and a job description, then suggests specific wording changes to improve ATS score.",
        inputSchema: {
            type: "object",
            properties: {
                cvText: { type: "string", description: "The current CV text" },
                jobDescription: { type: "string", description: "The job posting text" },
            },
            required: ["cvText", "jobDescription"],
        },
    },
];

/**
 * HANDLER: List available tools
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools: TOOLS };
});

/**
 * HANDLER: Execute tools
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case "analyze_cv": {
                const { cvText } = args as { cvText: string };
                // Placeholder logic: In a real app, this would use an LLM or specialized parser
                return {
                    content: [
                        {
                            type: "text",
                            text: `CV Analysis Summary:\n- Identified Skills: [Parsing...]\n- Experience: [Processing...]\n- Tips: "Update your summary to match modern industry standards."`,
                        },
                    ],
                };
            }

            case "search_linkedin_jobs": {
                const { keywords, location, limit = 5 } = args as { keywords: string; location?: string; limit?: number };
                // Placeholder logic: Integrate with an API or Scraper
                return {
                    content: [
                        {
                            type: "text",
                            text: `Searching for '${keywords}' jobs in '${location || "Global"}'...\nFound ${limit} potential matches. (Integration pending)`,
                        },
                    ],
                };
            }

            case "optimize_cv_for_job": {
                const { cvText, jobDescription } = args as { cvText: string; jobDescription: string };
                return {
                    content: [
                        {
                            type: "text",
                            text: `Optimization Report:\n1. Keyword Match: 65%\n2. Suggestion: Include more focus on 'Typescript' and 'Agentic workflows' as mentioned in the job description.`,
                        },
                    ],
                };
            }

            default:
                throw new Error(`Tool not found: ${name}`);
        }
    } catch (error: any) {
        return {
            isError: true,
            content: [{ type: "text", text: `Error: ${error.message}` }],
        };
    }
});

/**
 * START SERVER
 */
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("Claude Job Scout MCP Server running on stdio");
}

main().catch((error) => {
    console.error("Fatal error in main():", error);
    process.exit(1);
});
