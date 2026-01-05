import React, { useState, useEffect } from 'react';
import './MultiRangeSlider.css';

const MultiRangeSlider = ({ onChange }) => {
  const [fastFood, setFastFood] = useState(30);
  const [local, setLocal] = useState(40);
  const [upscale, setUpscale] = useState(30);

  useEffect(() => {
    onChange({ fastFood, local, upscale });
  }, [fastFood, local, upscale, onChange]);

  // Only handles should be clickable now; track click disabled.
  const startDrag = (e, which) => {
    e.preventDefault();
    const slider = e.currentTarget.parentElement.querySelector('.slider-track');
    const rect = slider.getBoundingClientRect();

    const getClientX = (event) => (event.touches ? event.touches[0].clientX : event.clientX);

    const onMove = (ev) => {
      const clientX = getClientX(ev);
      const percent = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      const value = Math.round(percent * 100);

      if (which === 'first') {
        // constrain first between 1 and (second - 1)
        const maxFirst = Math.max(1, fastFood + local - 1);
        const newFirst = Math.max(1, Math.min(maxFirst, value));
        const newLocal = Math.max(1, fastFood + local - newFirst);
        setFastFood(newFirst);
        setLocal(newLocal);
        setUpscale(100 - newFirst - newLocal);
      } else {
        // which === 'second'
        const first = fastFood;
        const minSecond = first + 1;
        const newSecond = Math.max(minSecond, Math.min(99, value));
        const newLocal = newSecond - first;
        setLocal(newLocal);
        setUpscale(100 - first - newLocal);
      }
    };

    const onEnd = () => {
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onEnd);
      document.removeEventListener('touchmove', onMove);
      document.removeEventListener('touchend', onEnd);
    };

    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onEnd);
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('touchend', onEnd);
  };

  const firstHandlePos = fastFood;
  const secondHandlePos = fastFood + local;

  return (
    <div className="multi-range-container">
      <div className="slider-track">
        {/* FastFood segment */}
        <div 
          className="slider-segment segment-ff"
          style={{ width: `${fastFood}%` }}
        />
        {/* Local segment */}
        <div 
          className="slider-segment segment-local"
          style={{ width: `${local}%` }}
        />
        {/* Upscale segment */}
        <div 
          className="slider-segment segment-upscale"
          style={{ width: `${upscale}%` }}
        />

        {/* First handle (fastFood/local boundary) */}
        <div
          className="slider-handle handle-first"
          style={{ left: `${firstHandlePos}%` }}
          onPointerDown={(e) => startDrag(e, 'first')}
          onTouchStart={(e) => startDrag(e, 'first')}
          title="Drag to adjust Fast Food / Local boundary"
        >
          <div className="handle-dot" />
        </div>

        {/* Second handle (local/upscale boundary) */}
        <div
          className="slider-handle handle-second"
          style={{ left: `${secondHandlePos}%` }}
          onPointerDown={(e) => startDrag(e, 'second')}
          onTouchStart={(e) => startDrag(e, 'second')}
          title="Drag to adjust Local / Upscale boundary"
        >
          <div className="handle-dot" />
        </div>
      </div>

      {/* Labels */}
      <div className="slider-labels">
        <div className="label-item">
          <span className="label-color ff-color" />
          <span className="label-text">Fast Food: {fastFood}%</span>
        </div>
        <div className="label-item">
          <span className="label-color local-color" />
          <span className="label-text">Local: {local}%</span>
        </div>
        <div className="label-item">
          <span className="label-color upscale-color" />
          <span className="label-text">Upscale: {upscale}%</span>
        </div>
      </div>
    </div>
  );
};

export default MultiRangeSlider;
