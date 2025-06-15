// Bagian Autentikasi dan Logout
document.addEventListener("DOMContentLoaded", async function () {
  try {
    const response = await fetch("/admin/dashboard", { method: "GET", credentials: "include" });
    if (!response.ok) throw new Error("Unauthorized");
    console.log("Dashboard Data loaded");

    // Memuat semua data setelah otentikasi berhasil
    loadUsers();
    loadTrashTypes();
    loadMerchandise();
    loadPickupRequests();
  } catch (error) {
    alert("Session expired! Please log in again.");
    window.location.href = "/admin/login";
  }
});

document.getElementById("logoutBtn").addEventListener("click", async function () {
  try {
    const response = await fetch("/admin/logout", { method: "POST", credentials: "include" });
    if (!response.ok) throw new Error("Logout failed");
    alert("Logout berhasil!");
    window.location.href = "/";
  } catch (error) {
    console.error("Logout error:", error);
  }
});

// FUNGSI NAVIGASI
function showSection(sectionId) {
  document.getElementById("manajemenPengguna").style.display = "none";
  document.getElementById("dataSampah").style.display = "none";
  document.getElementById("manajemenMerchandise").style.display = "none";
  document.getElementById("grafikMonitoring").style.display = "none";
  document.getElementById("permintaanJemput").style.display = "none";

  document.querySelectorAll(".sidebar .nav-link").forEach((link) => {
    link.classList.remove("active");
  });

  document.getElementById(sectionId).style.display = "block";
  document.getElementById(`nav-${sectionId}`).classList.add("active");
}

// ===============================================
// Bagian Users
// ===============================================
async function loadUsers() {
  try {
    const response = await fetch("/admin/users", { method: "GET", credentials: "include" });
    if (!response.ok) throw new Error("Gagal mengambil data pengguna");
    const users = await response.json();
    const tbody = document.getElementById("userTableBody");
    tbody.innerHTML = "";
    let totalPoints = 0;
    let totalBalance = 0;
    users.forEach((user) => {
      const points = user.points || 0;
      const balance = user.balance || 0;
      totalPoints += points;
      totalBalance += balance;
      tbody.innerHTML += `
        <tr>
          <td>${user.username}</td>
          <td>${user.email}</td>
          <td>${points}</td>
          <td>Rp ${balance.toLocaleString("id-ID")}</td>
          <td><button onclick="deleteUser(${user.id})" class="btn btn-danger btn-sm">Hapus</button></td>
        </tr>`;
    });
    document.getElementById("totalUsers").textContent = users.length;
    document.getElementById("totalPoints").textContent = totalPoints;
    document.getElementById("totalBalance").textContent = "Rp " + totalBalance.toLocaleString("id-ID");
  } catch (error) {
    console.error("Error loading users:", error);
  }
}

async function deleteUser(userId) {
  if (!confirm("Apakah Anda yakin ingin menghapus pengguna ini?")) return;
  try {
    const response = await fetch(`/admin/users/${userId}`, { method: "DELETE", credentials: "include" });
    if (!response.ok) throw new Error("Gagal menghapus pengguna");
    alert("Pengguna berhasil dihapus!");
    loadUsers();
  } catch (error) {
    console.error("Error deleting user:", error);
  }
}

// ===============================================
// Bagian Trash
// ===============================================
async function loadTrashTypes() {
  try {
    const response = await fetch("/admin/trash-types");
    if (!response.ok) throw new Error("Gagal mengambil data");
    const trashTypes = await response.json();
    const trashTableBody = document.getElementById("trashTableBody");
    trashTableBody.innerHTML = "";
    trashTypes.forEach((trash) => {
      trashTableBody.innerHTML += `
        <tr>
          <td>${trash.name}</td>
          <td>${trash.point_per_unit}</td>
          <td>${trash.unit}</td>
          <td><img src="${trash.cloudinary_url}" width="50" alt="${trash.name}"></td>
          <td>${trash.description}</td>
          <td>
            <button class="btn btn-warning btn-sm" onclick="editTrash(${trash.id}, '${trash.name}', ${trash.point_per_unit}, '${trash.unit}', \`${trash.description}\`)">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteTrash(${trash.id})">Hapus</button>
          </td>
        </tr>`;
    });
  } catch (error) {
    console.error("Error loading trash types:", error);
  }
}

function showAddTrashModal() {
  document.getElementById("trashId").value = "";
  document.getElementById("trashForm").reset();
  document.getElementById("modalTitle").innerText = "Tambah Jenis Sampah";
  document.getElementById("trashModal").style.display = "block";
}

function hideTrashModal() {
  document.getElementById("trashModal").style.display = "none";
}

function editTrash(id, name, pointPerUnit, unit, description) {
  document.getElementById("trashId").value = id;
  document.getElementById("trashName").value = name;
  document.getElementById("trashPointPerUnit").value = pointPerUnit;
  document.getElementById("trashUnit").value = unit;
  document.getElementById("trashDescription").value = description;
  document.getElementById("modalTitle").innerText = "Edit Jenis Sampah";
  document.getElementById("trashModal").style.display = "block";
}

async function saveTrash() {
  const id = document.getElementById("trashId").value;
  const name = document.getElementById("trashName").value;
  const pointPerUnit = document.getElementById("trashPointPerUnit").value;
  const unit = document.getElementById("trashUnit").value;
  const description = document.getElementById("trashDescription").value;
  const fileInput = document.getElementById("trashPicture");

  if (!name || !pointPerUnit || !unit) {
    alert("Nama, poin per unit, dan satuan harus diisi");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("point_per_unit", pointPerUnit);
  formData.append("unit", unit);
  formData.append("description", description || "");

  if (fileInput.files.length > 0) {
    formData.append("picture", fileInput.files[0]);
  }

  try {
    const method = id ? "PUT" : "POST";
    const url = id ? `/admin/trash-types/${id}` : "/admin/trash-types";
    const response = await fetch(url, { method, body: formData });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    hideTrashModal();
    loadTrashTypes();
  } catch (error) {
    console.error("Error saving trash type:", error);
    alert("Gagal menyimpan data: " + error.message);
  }
}

async function deleteTrash(id) {
  if (!confirm("Apakah Anda yakin ingin menghapus jenis sampah ini?")) return;
  try {
    const response = await fetch(`/admin/trash-types/${id}`, { method: "DELETE" });
    if (!response.ok) throw new Error("Gagal menghapus data");
    loadTrashTypes();
  } catch (error) {
    console.error("Error deleting trash type:", error);
    alert("Gagal menghapus data");
  }
}

// =======================================================
// BAGIAN MERCHANDISE
// =======================================================
async function loadMerchandise() {
  try {
    const response = await fetch("/admin/merchandise");
    if (!response.ok) throw new Error("Gagal mengambil data merchandise");
    const merchandise = await response.json();
    const tableBody = document.getElementById("merchTableBody");
    tableBody.innerHTML = "";
    if (merchandise.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="5" class="text-center p-5 text-muted"><i>Belum ada merchandise.</i></td></tr>`;
      return;
    }
    merchandise.forEach((merch) => {
      const row = `
        <tr>
          <td>${merch.name}</td>
          <td>${merch.point_cost}</td>
          <td><img src="${merch.image_url}" alt="${merch.name || "merch"}" class="merch-img"></td>
          <td>${merch.description || "-"}</td>
          <td>
            <button class="btn btn-warning btn-sm" onclick="editMerch(${merch.id}, '${merch.name}', ${merch.point_cost}, \`${merch.description || ""}\`)">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteMerchandise(${merch.id})">Hapus</button>
          </td>
        </tr>
      `;
      tableBody.innerHTML += row;
    });
  } catch (error) {
    console.error("Error loading merchandise:", error);
    document.getElementById("merchTableBody").innerHTML = `<tr><td colspan="5" class="text-center p-5 text-danger">Gagal memuat data.</td></tr>`;
  }
}

function showAddMerchModal() {
  document.getElementById("merchForm").reset();
  document.getElementById("merchId").value = "";
  document.getElementById("merchModalTitle").innerText = "Tambah Merchandise Baru";
  document.getElementById("merchModal").style.display = "block";
}

function hideMerchModal() {
  document.getElementById("merchModal").style.display = "none";
}

function editMerch(id, name, pointCost, description) {
  document.getElementById("merchId").value = id;
  document.getElementById("merchName").value = name;
  document.getElementById("merchPointCost").value = pointCost;
  document.getElementById("merchDescription").value = description;
  document.getElementById("merchPicture").value = "";
  document.getElementById("merchModalTitle").innerText = "Edit Merchandise";
  document.getElementById("merchModal").style.display = "block";
}

async function saveMerchandise() {
  const id = document.getElementById("merchId").value;
  const name = document.getElementById("merchName").value;
  const pointCost = document.getElementById("merchPointCost").value;
  const description = document.getElementById("merchDescription").value;
  const fileInput = document.getElementById("merchPicture");

  if (!name || !pointCost) {
    alert("Nama Merchandise dan Biaya Poin harus diisi");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("point_cost", pointCost);
  formData.append("description", description || "");

  if (fileInput.files.length > 0) {
    formData.append("picture", fileInput.files[0]);
  }

  try {
    const method = id ? "PUT" : "POST";
    const url = id ? `/admin/merchandise/${id}` : "/admin/merchandise";

    const response = await fetch(url, {
      method: method,
      body: formData,
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || "Gagal menyimpan data");
    }

    alert("Merchandise berhasil disimpan!");
    hideMerchModal();
    loadMerchandise();
  } catch (error) {
    console.error("Error saving merchandise:", error);
    alert("Gagal menyimpan: " + error.message);
  }
}

async function deleteMerchandise(id) {
  if (!confirm("Apakah Anda yakin ingin menghapus merchandise ini?")) return;
  try {
    const response = await fetch(`/admin/merchandise/${id}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || "Gagal menghapus data");
    }
    alert("Merchandise berhasil dihapus.");
    loadMerchandise();
  } catch (error) {
    console.error("Error deleting merchandise:", error);
    alert("Gagal menghapus: " + error.message);
  }
}

// =======================================================
// === BAGIAN PERMINTAAN JEMPUT (PICKUP REQUESTS) ===
// =======================================================
async function loadPickupRequests() {
  try {
    const response = await fetch("/api/admin/pickup-requests", { credentials: "include" });
    if (!response.ok) throw new Error("Gagal mengambil data permintaan jemput");
    const requests = await response.json();
    const tbody = document.getElementById("pickupRequestTableBody");
    tbody.innerHTML = "";

    if (requests.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center p-5 text-muted"><i>Tidak ada permintaan jemput saat ini.</i></td></tr>`;
      return;
    }

    requests.forEach((request) => {
      const requestDate = new Date(request.request_date).toLocaleString("id-ID", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });

      const statuses = {
        MENUNGGU_KONFIRMASI: "Menunggu Konfirmasi",
        DIPROSES: "Diproses",
        SELESAI: "Selesaikan",
        DIBATALKAN: "Batalkan",
      };

      let statusClass = "";
      switch (request.status) {
        case "MENUNGGU_KONFIRMASI":
          statusClass = "status-menunggu_konfirmasi";
          break;
        case "DIPROSES":
          statusClass = "status-diproses";
          break;
        case "SELESAI":
          statusClass = "status-selesai";
          break;
        case "DIBATALKAN":
          statusClass = "status-dibatalkan";
          break;
      }

      let optionsHtml = "";
      for (const key in statuses) {
        const selected = request.status === key ? "selected" : "";
        optionsHtml += `<option value="${key}" ${selected}>${statuses[key]}</option>`;
      }

      const isDisabled = request.status === "SELESAI" || request.status === "DIBATALKAN";

      const interactiveStatus = `
        <select 
          class="status-select ${statusClass}" 
          ${isDisabled ? "disabled" : ""} 
          onchange="updateRequestStatus(this, ${request.id})"
        >
          ${optionsHtml}
        </select>
      `;

      const row = `
        <tr>
          <td>${request.id}</td>
          <td>${request.username}</td>
          <td>${request.waste_category_name}</td>
          <td>${request.estimated_weight_g} g</td>
          <td>${request.address}</td>
          <td>${requestDate}</td>
          <td>${interactiveStatus}</td> 
        </tr>
      `;
      tbody.innerHTML += row;
    });
  } catch (error) {
    console.error("Error loading pickup requests:", error);
    document.getElementById("pickupRequestTableBody").innerHTML = `<tr><td colspan="7" class="text-center p-5 text-danger">Gagal memuat data.</td></tr>`;
  }
}

function updateRequestStatus(selectElement, requestId) {
  const newStatus = selectElement.value;

  if (newStatus === "SELESAI") {
    selectElement.blur();
    selesaikanPermintaan(requestId);
    return;
  }

  changeStatusOnly(requestId, newStatus);
}

async function changeStatusOnly(requestId, newStatus) {
  if (!confirm(`Anda yakin ingin mengubah status permintaan #${requestId} menjadi "${newStatus}"?`)) {
    loadPickupRequests();
    return;
  }

  try {
    const response = await fetch(`/api/admin/pickup-requests/${requestId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
      credentials: "include", // <-- DITAMBAHKAN
    });

    // Cek jika respons bukan JSON sebelum parsing
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Unknown error occurred");
      alert(result.message);
    } else {
      const text = await response.text();
      throw new Error("Server tidak merespons dengan JSON: " + text);
    }

    loadPickupRequests();
  } catch (error) {
    console.error("Gagal mengubah status:", error);
    alert("Gagal mengubah status: " + error.message);
    loadPickupRequests();
  }
}

async function selesaikanPermintaan(requestId) {
  const beratFinal = window.prompt("Masukkan berat akhir sampah yang sebenarnya (dalam gram):");

  if (beratFinal === null || beratFinal.trim() === "") {
    loadPickupRequests();
    return;
  }
  if (isNaN(beratFinal) || parseInt(beratFinal) < 0) {
    alert("Harap masukkan angka yang valid untuk berat.");
    loadPickupRequests();
    return;
  }

  try {
    const response = await fetch(`/api/admin/pickup-requests/${requestId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ final_weight_g: parseInt(beratFinal) }),
      credentials: "include", // <-- DITAMBAHKAN
    });

    // Cek jika respons bukan JSON sebelum parsing
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Unknown error occurred");
      alert(`Sukses! ${result.message}`);
    } else {
      const text = await response.text();
      throw new Error("Server tidak merespons dengan JSON: " + text);
    }

    loadPickupRequests();
    loadUsers();
  } catch (error) {
    console.error("Gagal menghubungi server:", error);
    alert("Gagal menyelesaikan permintaan: " + error.message);
    loadPickupRequests();
  }
}
