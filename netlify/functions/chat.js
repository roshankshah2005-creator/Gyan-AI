exports.handler = async function(event, context) {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: JSON.stringify({ error: 'Method Not Allowed' }) };
    }

    try {
        const { messages, persona } = JSON.parse(event.body || '{}');
        const apiKey = process.env.GROQ_API_KEY;

        if (!apiKey) {
            return {
                statusCode: 500,
                body: JSON.stringify({ reply: 'Server configuration error: GROQ_API_KEY is missing in Netlify settings.' })
            };
        }

        let systemPrompt = "You are Gyan, an intelligent multi-persona AI companion.";
        if (persona === 'Exam Prep Coach') systemPrompt = "You are an expert Exam Prep Coach, helping students break down derivations, concepts, and study schedules clearly.";
        else if (persona === 'Strict Professor') systemPrompt = "You are a strict, academic professor who demands rigorous precision and high standards.";
        else if (persona === 'Senior Tech Lead') systemPrompt = "You are a pragmatic Senior Tech Lead providing clean code architecture and debugging guidance.";
        else if (persona === 'Data Science Mentor') systemPrompt = "You are a Data Science Mentor explaining machine learning algorithms, Python, and data pipelines.";
        else if (persona === 'Creative Director') systemPrompt = "You are a Creative Director focusing on design principles, typography, and visual aesthetics.";

        const formattedMessages = [
            { role: "system", content: systemPrompt },
            ...messages
        ];

        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${apiKey}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model: "openai/gpt-oss-20b", // Correct active Groq model
                messages: formattedMessages,
                temperature: 0.6,
                max_completion_tokens: 2048
            })
        });

        const data = await response.json();
        
        if (data.error) {
            return { 
                statusCode: 400, 
                body: JSON.stringify({ reply: 'AI Error: ' + (data.error.message || JSON.stringify(data.error)) }) 
            };
        }

        const reply = data.choices && data.choices[0] && data.choices[0].message 
            ? data.choices[0].message.content 
            : "No response generated.";

        return {
            statusCode: 200,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reply: reply })
        };

    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ reply: 'Server error: ' + error.message })
        };
    }
};
