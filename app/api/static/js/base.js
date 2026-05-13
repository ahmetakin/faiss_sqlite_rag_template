function getInputValues() {
    const query = document.getElementById("queryInput").value.trim();
    const topK = parseInt(document.getElementById("topKInput").value || "5");

    if (!query) {
        alert("Lütfen bir soru veya arama sorgusu yaz.");
        return null;
    }

    return {
        query,
        topK
    };
}

function renderAnswer(text) {
    const answerBox = document.getElementById("answerBox");
    answerBox.textContent = text || "Cevap yok.";
}

function renderSources(sources) {
    const sourcesBox = document.getElementById("sourcesBox");

    if (!sources || sources.length === 0) {
        sourcesBox.innerHTML = "Kaynak bulunamadı.";
        return;
    }

    sourcesBox.innerHTML = sources.map((item, index) => {
        const title = item.title || "-";
        const productCode = item.product_code || "-";
        const matchType = item.match_type || "-";
        const selectedTool = item.selected_tool || "-";
        const imagePath = item.image_path || "-";
        const score = item.score !== undefined ? item.score : "-";
        const strictFamily = item.strict_family || "-";

        return `
            <div class="source-item">
                <div class="source-title">${index + 1}. ${title}</div>

                <div class="source-meta">
                    <span class="badge">${matchType}</span>
                    <span class="badge">${selectedTool}</span>
                    <span class="badge">${strictFamily}</span>
                </div>

                <div class="source-meta"><strong>Ürün kodu:</strong> ${productCode}</div>
                <div class="source-meta"><strong>Skor:</strong> ${score}</div>
                <div class="source-meta"><strong>Görsel:</strong> ${imagePath}</div>
            </div>
        `;
    }).join("");
}

async function runSearch() {
    const values = getInputValues();

    if (!values) {
        return;
    }

    renderAnswer("Search çalışıyor...");
    renderSources([]);

    try {
        const response = await fetch("/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: values.query,
                top_k: values.topK
            })
        });

        const data = await response.json();

        if (!response.ok) {
            renderAnswer(JSON.stringify(data, null, 2));
            return;
        }

        renderAnswer("Search tamamlandı. LLM cevabı üretilmedi.");
        renderSources(data.sources);

    } catch (error) {
        renderAnswer("Hata: " + error.message);
    }
}

async function runAsk() {
    const values = getInputValues();

    if (!values) {
        return;
    }

    renderAnswer("Ask çalışıyor...");
    renderSources([]);

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: values.query,
                top_k: values.topK
            })
        });

        const data = await response.json();

        if (!response.ok) {
            renderAnswer(JSON.stringify(data, null, 2));
            return;
        }

        renderAnswer(data.answer);
        renderSources(data.sources);

    } catch (error) {
        renderAnswer("Hata: " + error.message);
    }
}