export const initialState = {
  next_id:0,
  toasts:{}
};

export const ToastReducer = (currentState, action) => {
  // console.log(action)
  switch (action.type) {
    case "ADD_TOAST":
      return {
        ...currentState,
        next_id:currentState.next_id + 1,
        toasts:{...currentState.toasts, [currentState.next_id]:action.new_toast}
      };
    
    case "REMOVE_TOAST":
      return {
        ...currentState,
        toasts: Object.keys(currentState.toasts).reduce((acc,key)=>{
          if(key!==action.remove_key){
            acc[key] = currentState.toasts[key]
          }
          return acc
        },{}) 
      };

    default:
      throw new Error(`Unhandled action type: ${action.type}`);
  }
};