let file;

function pick() {
    document.getElementById("file").click();
}

document.getElementById("file").onchange = e => {
    file = e.target.files[0];
};

function analyze() {
    if (!file) return alert("Upload a file first");

    const data = new FormData();
    data.append("file", file);

    fetch("/upload", { method: "POST", body: data })
        .then(res => res.json())
        .then(show);
}

function show(data) {
    document.getElementById("result").hidden = false;

    document.getElementById("scoreBar").style.width = data.score + "%";
    document.getElementById("scoreText").innerText = data.score + "/100";

    const terms = document.getElementById("terms");
    terms.innerHTML = "";
    for (let k in data.terms) {
        terms.innerHTML += `<div><b>${k}</b><br>${data.terms[k]}</div>`;
    }

    const flags = document.getElementById("flags");
    flags.innerHTML = "";
    data.red_flags.forEach(f => flags.innerHTML += `<li>${f}</li>`);

    const recs = document.getElementById("recs");
    recs.innerHTML = "";
    data.recommendations.forEach(r => recs.innerHTML += `<li>${r}</li>`);
}
