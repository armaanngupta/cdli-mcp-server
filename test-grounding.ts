import { handler } from './src/tools/advanced-search/index.js';

async function runTests() {
    console.log("Testing misspellings...");
    
    // "nipuur" -> Nippur
    const res1 = await handler({ provenience: "nipuur" });
    console.log("Result for 'nipuur':", JSON.stringify(res1).substring(0, 300) + "...");
    
    // "uriii" -> Ur III
    const res2 = await handler({ period: "uriii" });
    console.log("Result for 'uriii':", JSON.stringify(res2).substring(0, 300) + "...");
    
    // "britsh museum" -> British Museum
    const res3 = await handler({ collection: "britsh museum" });
    console.log("Result for 'britsh museum':", JSON.stringify(res3).substring(0, 300) + "...");
}

runTests().catch(console.error);
