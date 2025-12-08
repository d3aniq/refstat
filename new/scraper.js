function extractData() {
  const widget = document.querySelector("#matchWidget");

  if (!widget || widget.innerText.trim().length < 10) {
    return; // widgeten ej klar
  }

  try {
    const info = {};

    info.home = widget.querySelector(".team-home")?.innerText.trim();
    info.away = widget.querySelector(".team-away")?.innerText.trim();
    info.score = widget.querySelector(".results")?.innerText.trim();
    info.datetime = widget.querySelector(".match-date")?.innerText.trim();
    info.arena = widget.querySelector(".arena-name")?.innerText.trim();

    // DOMARE
    info.referees = [...widget.querySelectorAll(".officials .official")]
      .map(e => e.innerText.trim());

    document.getElementById("info").innerText =
      JSON.stringify(info, null, 2);

  } catch (e) {
    document.getElementById("info").innerText = "Fel: " + e;
  }
}

// Lyssnar på ändringar i widgeten
const observer = new MutationObserver(extractData);
observer.observe(document.body, { childList: true, subtree: true });

setTimeout(extractData, 2000);
