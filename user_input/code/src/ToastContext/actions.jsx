export async function add_toast(dispatch,toast) {
  dispatch({ type: 'ADD_TOAST', new_toast: toast });
}

export async function remove_toast(dispatch, key) {
  dispatch({ type: 'REMOVE_TOAST',remove_key: key})
}