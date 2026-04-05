const state = {
  user: null,
  showUnavailableCourses: false,
};

function $(id) {
  return document.getElementById(id);
}

function msg(text, ok = true) {
  const el = document.createElement("div");
  el.className = ok ? "msg ok" : "msg err";
  el.textContent = text;
  $("messages").appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (state.user?.user_id) {
    headers["x-user-id"] = String(state.user.user_id);
  }
  return headers;
}

async function api(path, opts = {}) {
  const response = await fetch(path, {
    ...opts,
    headers: authHeaders(opts.headers || {}),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }

  const text = await response.text();
  if (!text) return null;
  return JSON.parse(text);
}

function setViewLoggedOut() {
  state.user = null;
  state.showUnavailableCourses = false;
  localStorage.removeItem("portalUser");
  $("auth-view").style.display = "grid";
  $("dashboard-view").style.display = "none";
  $("logout-btn").style.display = "none";
}

function setViewLoggedIn() {
  $("auth-view").style.display = "none";
  $("dashboard-view").style.display = "block";
  $("logout-btn").style.display = "inline-block";

  $("welcome").textContent = `Welcome, ${state.user.first_name} ${state.user.last_name}`;
  $("role-label").textContent = `Role: ${state.user.role}`;

  $("student-dashboard").style.display = "none";
  $("instructor-dashboard").style.display = "none";
  $("admin-dashboard").style.display = "none";

  if (state.user.role === "student") {
    $("student-dashboard").style.display = "grid";
    loadStudentData();
  }
  if (state.user.role === "instructor") {
    $("instructor-dashboard").style.display = "grid";
    loadInstructorData();
  }
  if (state.user.role === "admin") {
    $("admin-dashboard").style.display = "grid";
    loadAdminCourses();
    loadInstructors();
  }
}

function courseScheduleText(course) {
  const days = course.schedule_days || "TBA";
  const time = course.schedule_time || "TBA";
  const room = course.classroom_location || "TBA";
  return `${days} ${time} @ ${room}`;
}

async function loadStudentCatalog() {
  const courses = await api(
    `/student/catalog?include_unavailable=${state.showUnavailableCourses}`,
  );
  const body = $("student-catalog-body");
  body.innerHTML = "";
  $("toggle-unavailable-courses").textContent = state.showUnavailableCourses
    ? "Hide Unavailable Courses"
    : "View Unavailable Courses";

  courses.forEach((c) => {
    const tr = document.createElement("tr");
    const instructor = c.instructor_id ? `#${c.instructor_id}` : "Unassigned";
    const canEnroll = c.is_available;
    const actionLabel = canEnroll ? "Enroll" : "Full";
    tr.innerHTML = `
      <td>${c.course_id}</td>
      <td>${c.course_name}</td>
      <td>${c.department}</td>
      <td>${c.credits}</td>
      <td>${c.capacity} (${c.seats_remaining} seats left)</td>
      <td>${instructor}</td>
      <td>${courseScheduleText(c)}</td>
      <td><button data-course-id="${c.course_id}" ${canEnroll ? "" : "disabled"}>${actionLabel}</button></td>
    `;
    tr.querySelector("button").addEventListener("click", async () => {
      try {
        await api(`/enrollments?course_id=${c.course_id}`, { method: "POST" });
        msg("Enrolled successfully");
        loadStudentData();
      } catch (e) {
        msg(`Enroll failed: ${e.message}`, false);
      }
    });
    body.appendChild(tr);
  });
}

async function loadStudentCourses() {
  const courses = await api("/student/courses");
  const ul = $("student-my-courses");
  ul.innerHTML = "";
  courses.forEach((c) => {
    const li = document.createElement("li");
    li.innerHTML = `${c.course_name} (${c.department}) <button data-course-id="${c.course_id}">Drop</button>`;
    li.querySelector("button").addEventListener("click", async () => {
      try {
        await api(`/enrollments?course_id=${c.course_id}`, { method: "DELETE" });
        msg("Course dropped");
        loadStudentData();
      } catch (e) {
        msg(`Drop failed: ${e.message}`, false);
      }
    });
    ul.appendChild(li);
  });
}

async function loadStudentGrades() {
  const grades = await api("/student/grades");
  const ul = $("student-grades");
  ul.innerHTML = "";
  grades.forEach((g) => {
    const li = document.createElement("li");
    li.textContent = `${g.course_name}: ${g.grade}`;
    ul.appendChild(li);
  });
}

async function loadStudentSchedule() {
  const rows = await api("/student/schedule");
  const ul = $("student-schedule");
  ul.innerHTML = "";
  rows.forEach((row) => {
    const li = document.createElement("li");
    li.textContent = `${row.course_name}: ${row.days || "TBA"} ${row.time || "TBA"} (${row.classroom_location || "TBA"})`;
    ul.appendChild(li);
  });
}

async function loadStudentData() {
  try {
    await Promise.all([
      loadStudentCatalog(),
      loadStudentCourses(),
      loadStudentGrades(),
      loadStudentSchedule(),
    ]);
  } catch (e) {
    msg(`Student dashboard error: ${e.message}`, false);
  }
}

async function loadInstructorCourses() {
  try {
    const courses = await api("/instructor/courses");
    const ul = $("instructor-courses");
    if (!ul) {
      throw new Error("Instructor dashboard UI not found. Refresh the page.");
    }
    ul.innerHTML = "";

    courses.forEach((c) => {
      const li = document.createElement("li");
      li.textContent = `#${c.course_id} ${c.course_name} - ${courseScheduleText(c)}`;
      ul.appendChild(li);
    });
  } catch (e) {
    msg(`Instructor courses error: ${e.message}`, false);
  }
}

async function loadInstructorAssignmentsAndGrades() {
  try {
    const payload = await api("/instructor/dashboard");
    const body = $("instructor-assignment-body");
    if (!body) {
      throw new Error("Instructor grade table not found. Refresh the page.");
    }
    body.innerHTML = "";

    payload.courses.forEach((course) => {
      if (!course.students.length) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${course.course_id}</td>
          <td>${course.course_name}</td>
          <td>-</td>
          <td>No enrolled students</td>
          <td>-</td>
          <td>-</td>
          <td>No current grade</td>
        `;
        body.appendChild(tr);
        return;
      }

      course.students.forEach((student) => {
        const tr = document.createElement("tr");
        const gradeIdText = student.grade_id ? String(student.grade_id) : "-";
        tr.innerHTML = `
          <td>${course.course_id}</td>
          <td>${course.course_name}</td>
          <td>${student.student_id}</td>
          <td>${student.student_name}</td>
          <td>${student.student_email}</td>
          <td>${gradeIdText}</td>
          <td>${student.grade || "No current grade"}</td>
        `;

        body.appendChild(tr);
      });
    });
  } catch (e) {
    msg(`Instructor dashboard error: ${e.message}`, false);
  }
}

async function loadInstructorData() {
  await Promise.all([loadInstructorCourses(), loadInstructorAssignmentsAndGrades()]);
}

async function loadAdminCourses() {
  try {
    const courses = await api("/courses");
    const ul = $("admin-courses");
    ul.innerHTML = "";
    courses.forEach((c) => {
      const li = document.createElement("li");
      li.textContent = `#${c.course_id} ${c.course_name} (${c.department}) credits:${c.credits} cap:${c.capacity} instructor:${c.instructor_id || "none"} schedule:${courseScheduleText(c)}`;
      ul.appendChild(li);
    });
  } catch (e) {
    msg(`Admin courses error: ${e.message}`, false);
  }
}

async function loadInstructors() {
  try {
    const instructors = await api("/instructors");
    const ul = $("admin-instructors");
    ul.innerHTML = "";
    instructors.forEach((ins) => {
      const li = document.createElement("li");
      li.textContent = `#${ins.instructor_id} ${ins.first_name} ${ins.last_name} (${ins.email}) dept:${ins.department || "n/a"} office:${ins.office_location || "n/a"}`;
      ul.appendChild(li);
    });
  } catch (e) {
    msg(`Instructor list error: ${e.message}`, false);
  }
}

async function handleLogin() {
  const email = $("login-email").value.trim();
  const password = $("login-password").value.trim();
  if (!email || !password) {
    msg("Login email and password are required", false);
    return;
  }

  try {
    const user = await api("/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    state.user = user;
    localStorage.setItem("portalUser", JSON.stringify(user));
    setViewLoggedIn();
    msg("Login successful");
  } catch (e) {
    msg(`Login failed: ${e.message}`, false);
  }
}

async function handleSignup() {
  const payload = {
    role: $("signup-role").value,
    first_name: $("signup-first").value.trim(),
    last_name: $("signup-last").value.trim(),
    email: $("signup-email").value.trim(),
    password: $("signup-password").value.trim(),
  };

  if (!payload.first_name || !payload.last_name || !payload.email || !payload.password) {
    msg("All sign up fields are required", false);
    return;
  }

  try {
    await api("/auth/signup", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    msg("Account created. You can now login.");
  } catch (e) {
    msg(`Sign up failed: ${e.message}`, false);
  }
}

function bindStudentActions() {
  $("refresh-catalog").onclick = loadStudentCatalog;
  $("toggle-unavailable-courses").onclick = async () => {
    state.showUnavailableCourses = !state.showUnavailableCourses;
    await loadStudentCatalog();
  };
  $("refresh-my-courses").onclick = loadStudentCourses;
  $("refresh-grades").onclick = loadStudentGrades;
  $("refresh-schedule").onclick = loadStudentSchedule;
}

function bindInstructorActions() {
  const refreshCoursesBtn = $("refresh-instructor-courses");
  const refreshDashboardBtn = $("refresh-instructor-dashboard");
  const createGradeBtn = $("create-grade");
  const updateGradeBtn = $("update-grade");
  const deleteGradeBtn = $("delete-grade");

  if (refreshCoursesBtn) {
    refreshCoursesBtn.onclick = loadInstructorCourses;
  }
  if (refreshDashboardBtn) {
    refreshDashboardBtn.onclick = loadInstructorAssignmentsAndGrades;
  }

  if (createGradeBtn) {
    createGradeBtn.onclick = async () => {
    const student_id = parseInt($("grade-student-id").value, 10);
    const course_id = parseInt($("grade-course-id").value, 10);
    const grade = $("grade-value").value.trim();
    if (!student_id || !course_id || !grade) {
      msg("Student ID, Course ID, and Grade are required", false);
      return;
    }
    try {
      await api("/instructor/grades", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ student_id, course_id, grade }),
      });
      msg("Grade created");
      loadInstructorAssignmentsAndGrades();
    } catch (e) {
      msg(`Create grade failed: ${e.message}`, false);
    }
    };
  }

  if (updateGradeBtn) {
    updateGradeBtn.onclick = async () => {
    const student_id = parseInt($("grade-student-id").value, 10);
    const course_id = parseInt($("grade-course-id").value, 10);
    const grade = $("grade-value").value.trim();
    if (!student_id || !course_id || !grade) {
      msg("Student ID, Course ID, and Grade are required", false);
      return;
    }
    try {
      await api("/instructor/grades", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ student_id, course_id, grade }),
      });
      msg("Grade updated");
      loadInstructorAssignmentsAndGrades();
    } catch (e) {
      msg(`Update grade failed: ${e.message}`, false);
    }
    };
  }

  if (deleteGradeBtn) {
    deleteGradeBtn.onclick = async () => {
    const gradeId = parseInt($("delete-grade-id").value, 10);
    if (!gradeId) {
      msg("Grade ID required", false);
      return;
    }
    try {
      await api(`/instructor/grades/${gradeId}`, { method: "DELETE" });
      msg("Grade deleted");
      loadInstructorAssignmentsAndGrades();
    } catch (e) {
      msg(`Delete grade failed: ${e.message}`, false);
    }
    };
  }
}

function bindAdminActions() {
  $("refresh-admin-courses").onclick = loadAdminCourses;
  $("refresh-instructors").onclick = loadInstructors;

  $("create-course").onclick = async () => {
    const payload = {
      course_name: $("course-name").value.trim(),
      department: $("course-department").value.trim(),
      credits: parseInt($("course-credits").value, 10),
      capacity: parseInt($("course-capacity").value, 10),
    };
    if (!payload.course_name || !payload.department || !payload.credits || !payload.capacity) {
      msg("Course fields are required", false);
      return;
    }
    try {
      await api("/courses", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      msg("Course created");
      loadAdminCourses();
    } catch (e) {
      msg(`Create course failed: ${e.message}`, false);
    }
  };

  $("update-course").onclick = async () => {
    const id = parseInt($("edit-course-id").value, 10);
    if (!id) {
      msg("Course ID is required for update", false);
      return;
    }

    const payload = {
      course_name: $("edit-course-name").value.trim() || null,
      department: $("edit-course-department").value.trim() || null,
      credits: $("edit-course-credits").value ? parseInt($("edit-course-credits").value, 10) : null,
      capacity: $("edit-course-capacity").value ? parseInt($("edit-course-capacity").value, 10) : null,
    };

    try {
      await api(`/courses/${id}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      msg("Course updated");
      loadAdminCourses();
    } catch (e) {
      msg(`Update course failed: ${e.message}`, false);
    }
  };

  $("delete-course").onclick = async () => {
    const id = parseInt($("edit-course-id").value, 10);
    if (!id) {
      msg("Course ID is required for delete", false);
      return;
    }
    try {
      await api(`/courses/${id}`, { method: "DELETE" });
      msg("Course deleted");
      loadAdminCourses();
    } catch (e) {
      msg(`Delete course failed: ${e.message}`, false);
    }
  };

  $("update-instructor-info").onclick = async () => {
    const instructorId = parseInt($("ins-id").value, 10);
    const department = $("ins-department").value.trim();
    const office_location = $("ins-office").value.trim();

    if (!instructorId) {
      msg("Instructor ID is required", false);
      return;
    }
    if (!department && !office_location) {
      msg("Department or office location is required", false);
      return;
    }

    try {
      await api(`/admin/instructors/${instructorId}/info`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          department: department || null,
          office_location: office_location || null,
        }),
      });
      msg("Instructor info updated");
      loadInstructors();
    } catch (e) {
      msg(`Update instructor info failed: ${e.message}`, false);
    }
  };

  $("delete-instructor").onclick = async () => {
    const id = parseInt($("delete-instructor-id").value, 10);
    if (!id) {
      msg("Instructor ID required", false);
      return;
    }
    try {
      await api(`/admin/instructors/${id}`, { method: "DELETE" });
      msg("Instructor deleted");
      loadInstructors();
      loadAdminCourses();
    } catch (e) {
      msg(`Delete instructor failed: ${e.message}`, false);
    }
  };

  $("assign-instructor").onclick = async () => {
    const courseId = parseInt($("assign-course-id").value, 10);
    const instructorId = parseInt($("assign-instructor-id").value, 10);
    if (!courseId || !instructorId) {
      msg("Course ID and Instructor ID are required", false);
      return;
    }
    try {
      await api(`/admin/courses/${courseId}/assign-instructor`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ instructor_id: instructorId }),
      });
      msg("Instructor assigned");
      loadAdminCourses();
    } catch (e) {
      msg(`Assign instructor failed: ${e.message}`, false);
    }
  };

  $("update-instructor-assignment").onclick = async () => {
    const courseId = parseInt($("assign-course-id").value, 10);
    const instructorId = parseInt($("assign-instructor-id").value, 10);
    if (!courseId || !instructorId) {
      msg("Course ID and Instructor ID are required", false);
      return;
    }
    try {
      await api(`/admin/courses/${courseId}/update-instructor`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ instructor_id: instructorId }),
      });
      msg("Instructor assignment updated");
      loadAdminCourses();
    } catch (e) {
      msg(`Update instructor assignment failed: ${e.message}`, false);
    }
  };

  const getSchedulePayload = () => {
    const courseId = parseInt($("schedule-course-id").value, 10);
    const schedule_days = $("schedule-days").value.trim();
    const schedule_time = $("schedule-time").value.trim();
    const classroom_location = $("schedule-room").value.trim();

    return {
      courseId,
      payload: { schedule_days, schedule_time, classroom_location },
    };
  };

  $("save-schedule").onclick = async () => {
    const { courseId, payload } = getSchedulePayload();
    const { schedule_days, schedule_time, classroom_location } = payload;
    if (!courseId || !schedule_days || !schedule_time || !classroom_location) {
      msg("Course ID, days, time, and classroom are required", false);
      return;
    }
    try {
      await api(`/admin/courses/${courseId}/schedule`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      msg("Schedule updated");
      loadAdminCourses();
    } catch (e) {
      msg(`Schedule update failed: ${e.message}`, false);
    }
  };

  $("update-schedule").onclick = async () => {
    const { courseId, payload } = getSchedulePayload();
    const { schedule_days, schedule_time, classroom_location } = payload;
    if (!courseId) {
      msg("Course ID is required", false);
      return;
    }
    if (!schedule_days && !schedule_time && !classroom_location) {
      msg("Provide at least one field to update", false);
      return;
    }

    const updatePayload = {
      schedule_days: schedule_days || null,
      schedule_time: schedule_time || null,
      classroom_location: classroom_location || null,
    };

    try {
      await api(`/admin/courses/${courseId}/schedule`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(updatePayload),
      });
      msg("Created schedule updated");
      loadAdminCourses();
    } catch (e) {
      msg(`Update created schedule failed: ${e.message}`, false);
    }
  };

  $("delete-schedule").onclick = async () => {
    const courseId = parseInt($("schedule-course-id").value, 10);
    if (!courseId) {
      msg("Course ID is required", false);
      return;
    }

    try {
      await api(`/admin/courses/${courseId}/schedule`, {
        method: "DELETE",
      });
      msg("Schedule deleted");
      loadAdminCourses();
    } catch (e) {
      msg(`Delete schedule failed: ${e.message}`, false);
    }
  };
}

function bindGlobalActions() {
  $("login-btn").onclick = handleLogin;
  $("signup-btn").onclick = handleSignup;
  $("logout-btn").onclick = () => {
    setViewLoggedOut();
    msg("Logged out");
  };
}

document.addEventListener("DOMContentLoaded", async () => {
  bindGlobalActions();
  bindStudentActions();
  bindInstructorActions();
  bindAdminActions();

  const saved = localStorage.getItem("portalUser");
  if (!saved) {
    setViewLoggedOut();
    return;
  }

  try {
    state.user = JSON.parse(saved);
    await api("/me");
    setViewLoggedIn();
  } catch {
    setViewLoggedOut();
  }
});
