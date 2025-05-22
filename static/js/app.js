// Bagian Users
document.addEventListener("DOMContentLoaded", async function () {
  try {
    const response = await fetch("/admin/dashboard", { method: "GET", credentials: "include" });
    if (!response.ok) throw new Error("Unauthorized");
    console.log("Dashboard Data loaded");
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

async function loadUsers() {
  try {
    const response = await fetch("/admin/users", {
      method: "GET",
      credentials: "include",
    });

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

function showSection(sectionId) {
  document.getElementById("manajemenPengguna").style.display = "none";
  document.getElementById("dataSampah").style.display = "none";
  document.getElementById("grafikMonitoring").style.display = "none";
  document.getElementById(sectionId).style.display = "block";
}

loadUsers();
// Akhir Bagian Users

// Bagian Trash
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
            <button class="btn btn-warning btn-sm" onclick="editTrash(${trash.id}, '${trash.name}', ${trash.point_per_unit}, '${trash.unit}', '${trash.description}')">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteTrash(${trash.id})">Hapus</button>
          </td>
        </tr>`;
    });
  } catch (error) {
    console.error("Error loading trash types:", error);
    alert("Gagal memuat data jenis sampah");
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

    const response = await fetch(url, {
      method,
      body: formData,
    });

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
    const response = await fetch(`/admin/trash-types/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error("Gagal menghapus data");
    }

    loadTrashTypes();
  } catch (error) {
    console.error("Error deleting trash type:", error);
    alert("Gagal menghapus data");
  }
}

// Load data saat pertama kali
document.addEventListener("DOMContentLoaded", loadTrashTypes);
