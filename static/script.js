// static/script.js

document.addEventListener("DOMContentLoaded", function () {
  // Make sure graph_json is correctly passed from the backend
  var graphJson = JSON.parse(document.getElementById("graphJson").textContent);
  console.log(graphJson); // ตรวจสอบค่า
  Plotly.newPlot("graph", graphJson.data, graphJson.layout);
});
function validateForm() {
  const checkboxes = document.querySelectorAll(
    'input[name="column_name"]:checked'
  );
  if (checkboxes.length === 0) {
    alert("กรุณาเลือกคอลัมน์อย่างน้อยหนึ่งคอลัมน์");
    return false; // ห้ามส่งฟอร์ม
  }
  return true; // อนุญาตให้ส่งฟอร์ม
}
