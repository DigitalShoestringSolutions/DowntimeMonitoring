import React from 'react';
import { ToastReducer, initialState } from './reducer';
import { remove_toast } from './actions'
import ToastContainer from 'react-bootstrap/ToastContainer'
import Toast from 'react-bootstrap/Toast'

const ToastStateContext = React.createContext();
const ToastDispatchContext = React.createContext();

export function useToastState() {
  const context = React.useContext(ToastStateContext);
  if (context === undefined) {
    throw new Error("useToastState must be used within a ToastProvider");
  }

  return context;
}

export function useToastDispatch() {
  const context = React.useContext(ToastDispatchContext);
  if (context === undefined) {
    throw new Error("useToastDispatch must be used within a ToastProvider");
  }

  return context;
}

export const ToastProvider = ({ children, position = "bottom-end" }) => {
  const [user, dispatch] = React.useReducer(ToastReducer, initialState);

  return (
    <ToastStateContext.Provider value={user}>
      <ToastDispatchContext.Provider value={dispatch}>
        {children}
        <ToastContainer position={position} className="p-3">
          <Toasts />
        </ToastContainer>
      </ToastDispatchContext.Provider>
    </ToastStateContext.Provider>
  );
};

function Toasts(props) {
  let { toasts } = useToastState()
  let dispatch = useToastDispatch()
  return <>
    {Object.keys(toasts).map(key => (<ToastTemplate key={key} toast={toasts[key]} remove={async () => await remove_toast(dispatch, key)} />))}
  </>
}

function ToastTemplate({ toast, remove }) {
  return <Toast onClose={remove} delay={3000} autohide>
    <Toast.Header>
      <strong className="me-auto">{toast.header}</strong>
    </Toast.Header>
    {toast.body?<Toast.Body>{toast.body}</Toast.Body>:""}
  </Toast>
}