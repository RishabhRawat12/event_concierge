import { 
  onAuthStateChanged, 
  signInWithPopup, 
  GoogleAuthProvider, 
  signOut,
  User
} from 'firebase/auth';
import { auth } from './firebase';

const provider = new GoogleAuthProvider();

export const loginWithGoogle = async () => {
  try {
    const result = await signInWithPopup(auth, provider);
    return result.user;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
};

export const logout = async () => {
  try {
    await signOut(auth);
  } catch (error) {
    console.error('Logout failed:', error);
    throw error;
  }
};

export const subscribeToAuthChanges = (callback: (user: User | null) => void) => {
  return onAuthStateChanged(auth, callback);
};

export const getAuthToken = async () => {
  const user = auth.currentUser;
  if (!user) return null;
  return await user.getIdToken();
};
