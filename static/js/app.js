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
    const response = await fetch("/admin/users", { method: "GET", credentials: "include" });
    if (!response.ok) throw new Error("Gagal mengambil data pengguna");

    const users = await response.json();
    const userTableBody = document.getElementById("userTableBody");
    userTableBody.innerHTML = "";

    users.forEach((user) => {
      userTableBody.innerHTML += `
                      <tr>
                          <td>${user.username}</td>
                          <td>${user.email}</td>
                          <td><button onclick="deleteUser(${user.id})" class="btn btn-danger btn-sm">Hapus</button></td>
                      </tr>`;
    });
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
          <td>${trash.price}</td>
          <td>${trash.unit}</td>
          <td><img src="${trash.picture}" width="50"></td>
          <td>${trash.description}</td>
          <td>
            <button class="btn btn-warning btn-sm" onclick="editTrash(${trash.id}, '${trash.name}', ${trash.price}, '${trash.unit}', '${trash.picture}', '${trash.description}')">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteTrash(${trash.id})">Hapus</button>
          </td>
        </tr>`;
    });
  } catch (error) {
    console.error("Error loading trash types:", error);
  }
}

function showAddTrashModal() {
  document.getElementById("trashModal").style.display = "block";
  document.getElementById("modalTitle").innerText = "Tambah Jenis Sampah";
}

function hideTrashModal() {
  document.getElementById("trashModal").style.display = "none";
}

function editTrash(id, name, price, unit, picture, description) {
  document.getElementById("trashId").value = id;
  document.getElementById("trashName").value = name;
  document.getElementById("trashPrice").value = price;
  document.getElementById("trashUnit").value = unit;
  document.getElementById("trashDescription").value = description;

  // Jangan set value untuk input file karena tidak diperbolehkan
  document.getElementById("trashPicture").value = "";

  document.getElementById("modalTitle").innerText = "Edit Jenis Sampah";
  document.getElementById("trashModal").style.display = "block";
}

async function saveTrash() {
  const id = document.getElementById("trashId").value;
  const name = document.getElementById("trashName").value;
  const price = document.getElementById("trashPrice").value;
  const unit = document.getElementById("trashUnit").value;
  const description = document.getElementById("trashDescription").value;
  const fileInput = document.getElementById("trashPicture");

  const formData = new FormData();
  formData.append("name", name);
  formData.append("price", price);
  formData.append("unit", unit);
  formData.append("description", description);

  // Tambah file jika ada
  if (fileInput.files.length > 0) {
    formData.append("picture", fileInput.files[0]);
  }

  const method = id ? "PUT" : "POST";
  const url = id ? `/admin/trash-types/${id}` : "/admin/trash-types";

  await fetch(url, {
    method,
    body: formData, // Kirim sebagai FormData
  });

  hideTrashModal();
  loadTrashTypes();
}

async function deleteTrash(id) {
  if (!confirm("Hapus jenis sampah ini?")) return;

  await fetch(`/admin/trash-types/${id}`, { method: "DELETE" });
  loadTrashTypes();
}

loadTrashTypes();
// Akhir Bagian Trash
