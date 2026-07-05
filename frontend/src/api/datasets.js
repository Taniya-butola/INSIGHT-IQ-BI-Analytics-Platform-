import client from "./client";

export const listDatasets = () => client.get("/datasets").then((r) => r.data.datasets);

export const uploadDataset = (file, onProgress) => {
  const formData = new FormData();
  formData.append("file", file);
  return client
    .post("/datasets/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) {
          onProgress(Math.round((evt.loaded / evt.total) * 100));
        }
      },
    })
    .then((r) => r.data.dataset);
};

export const deleteDataset = (id) => client.delete(`/datasets/${id}`).then((r) => r.data);

export const getDataset = (id) => client.get(`/datasets/${id}`).then((r) => r.data.dataset);

export const validateDataset = (id) =>
  client.post(`/datasets/${id}/validate`).then((r) => r.data);

export const getValidation = (id) =>
  client.get(`/datasets/${id}/validation`).then((r) => r.data);

export const cleanDataset = (id) => client.post(`/datasets/${id}/clean`).then((r) => r.data);

export const getCleaning = (id) => client.get(`/datasets/${id}/cleaning`).then((r) => r.data);

export const previewDataset = (id, stage = "raw") =>
  client.get(`/datasets/${id}/preview`, { params: { stage } }).then((r) => r.data);

export const runEda = (id) => client.post(`/datasets/${id}/eda`).then((r) => r.data);

export const getEda = (id) => client.get(`/datasets/${id}/eda`).then((r) => r.data);

export const getDashboardFilters = (id) =>
  client.get(`/datasets/${id}/dashboard/filters`).then((r) => r.data);

export const getDashboard = (id, filters = {}) =>
  client
    .get(`/datasets/${id}/dashboard`, {
      params: {
        region: filters.region || undefined,
        category: filters.category || undefined,
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
      },
    })
    .then((r) => r.data.dashboard);

export const runPredictive = (id) => client.post(`/datasets/${id}/predictive`).then((r) => r.data);

export const getPredictive = (id) => client.get(`/datasets/${id}/predictive`).then((r) => r.data);

export const runInsights = (id) => client.post(`/datasets/${id}/insights`).then((r) => r.data);

export const getInsights = (id) => client.get(`/datasets/${id}/insights`).then((r) => r.data);

export const listReportTypes = () =>
  client.get("/datasets/report-types").then((r) => r.data.report_types);

export const downloadReport = async (id, reportType, format, filenameHint) => {
  const response = await client.get(`/datasets/${id}/reports/${reportType}`, {
    params: { format },
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `${filenameHint}_${reportType}.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const getChatMessages = (id) => client.get(`/datasets/${id}/messages`).then((r) => r.data.messages);

export const clearChatMessages = (id) => client.delete(`/datasets/${id}/messages`).then((r) => r.data);

export const askQuestion = (id, question) =>
  client.post(`/datasets/${id}/ask`, { question }).then((r) => r.data);
