import axios from 'axios';

const LOG_API_URL = 'http://20.244.56.144/evaluation-service/logs';

const accessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiYXVkIjoiaHR0cDovLzIwLjI0NC41Ni4xNDQvZXZhbHVhdGlvbi1zZXJ2aWNlIiwiZW1haWwiOiJzaHlhbXN1bmRhcnllZGxhMUBnbWFpbC5jb20iLCJleHAiOjE3NTA5MjEwMzMsImlhdCI6MTc1MDkyMDEzMywiaXNzIjoiQWZmb3JkIE1lZGljYWwgVGVjaG5vbG9naWVzIFByaXZhdGUgTGltaXRlZCIsImp0aSI6ImQ3NDlhMTE4LTMwYTYtNGQwMi1iODcxLWVhMTMzMmQzNWFhYSIsImxvY2FsZSI6ImVuLUlOIiwibmFtZSI6InlhZGxhIHN5YW0gc3VuZGFyIG1hbmkga3Jpc2huYSIsInN1YiI6IjI5MGFkZjE4LWM1MjItNGJjMi1iMjM3LTgxOWVhZmJkYjkwOCJ9LCJlbWFpbCI6InNoeWFtc3VuZGFyeWVkbGExQGdtYWlsLmNvbSIsIm5hbWUiOiJ5YWRsYSBzeWFtIHN1bmRhciBtYW5pIGtyaXNobmEiLCJyb2xsTm8iOiIyMmE5MWE0NDUxIiwiYWNjZXNzQ29kZSI6Ik5Gd2dSVCIsImNsaWVudElEIjoiMjkwYWRmMTgtYzUyMi00YmMyLWIyMzctODE5ZWFmYmRiOTA4IiwiY2xpZW50U2VjcmV0IjoiRHp4dGJERUJuSmRZUENuaiJ9.EaGPbCCmDvhIhjJizd0SC-MfQkzWzuzns9HtPDVsSlY";

const validStacks = ["backend", "frontend"];
const validLevels = ["debug", "info", "warn", "error", "fatal"];
const validPackages = [
  "cache", "controller", "cron_job", "db", "domain", "handler", "repository", "route", "service",
  "api", "component", "hook", "page", "state", "style",
  "auth", "config", "middleware", "utils"
];

export async function Log(stack: string, level: string, packageName: string, message: string) {
  if (!validStacks.includes(stack)) throw new Error("Invalid stack");
  if (!validLevels.includes(level)) throw new Error("Invalid level");
  if (!validPackages.includes(packageName)) throw new Error("Invalid package");

  try {
    const response = await axios.post(
      LOG_API_URL,
      {
        stack,
        level,
        package: packageName,
        message
      },
      {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      }
    );

    return response.data;
  } catch (error: any) {
    console.error("Logging failed:", error.response?.data || error.message);
  }
} 