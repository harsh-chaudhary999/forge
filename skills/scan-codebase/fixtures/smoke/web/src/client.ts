export async function loadHello(): Promise<boolean> {
  const response = await fetch('/api/hello');
  return response.ok;
}
