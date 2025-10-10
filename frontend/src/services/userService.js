import API from "./api";

export const getCurrentUser = async (token) => {
  const res = await API.get("/users/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};
